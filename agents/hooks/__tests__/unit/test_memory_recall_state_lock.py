import fcntl

import memory_recall_debounce
import pytest


@pytest.fixture
def short_lock_timeout(monkeypatch):
    monkeypatch.setattr(
        memory_recall_debounce, "STATE_LOCK_ACQUISITION_TIMEOUT_SECONDS", 0.05
    )


def hold_lock_on_state(state_path):
    lock_file = memory_recall_debounce.state_lock_path_for_session_state(
        state_path
    ).open("w")
    fcntl.flock(lock_file, fcntl.LOCK_EX)
    return lock_file


class TestStateLockPath:
    def test_lock_path_is_a_sibling_of_the_state_file(self, tmp_path):
        state_path = tmp_path / "memory-recall-session.json"
        lock_path = memory_recall_debounce.state_lock_path_for_session_state(state_path)
        assert lock_path.parent == state_path.parent
        assert lock_path.name == "memory-recall-session.json.lock"

    def test_lock_path_never_matches_the_state_file_glob(self, tmp_path):
        state_path = tmp_path / "memory-recall-session.json"
        lock_path = memory_recall_debounce.state_lock_path_for_session_state(state_path)
        assert not lock_path.match("memory-recall-*.json")


class TestAcquireExclusiveLockBeforeDeadline:
    def test_free_lock_is_acquired(self, tmp_path, short_lock_timeout):
        state_path = tmp_path / "memory-recall-session.json"
        lock_file = memory_recall_debounce.state_lock_path_for_session_state(
            state_path
        ).open("w")
        assert memory_recall_debounce.acquire_exclusive_lock_before_deadline(lock_file)

    def test_held_lock_is_refused_at_the_deadline(self, tmp_path, short_lock_timeout):
        state_path = tmp_path / "memory-recall-session.json"
        holder = hold_lock_on_state(state_path)
        contender = memory_recall_debounce.state_lock_path_for_session_state(
            state_path
        ).open("w")
        try:
            assert not memory_recall_debounce.acquire_exclusive_lock_before_deadline(
                contender
            )
        finally:
            fcntl.flock(holder, fcntl.LOCK_UN)
            holder.close()
            contender.close()

    def test_released_lock_is_acquired_again(self, tmp_path, short_lock_timeout):
        state_path = tmp_path / "memory-recall-session.json"
        holder = hold_lock_on_state(state_path)
        fcntl.flock(holder, fcntl.LOCK_UN)
        holder.close()
        contender = memory_recall_debounce.state_lock_path_for_session_state(
            state_path
        ).open("w")
        assert memory_recall_debounce.acquire_exclusive_lock_before_deadline(contender)


class TestExclusiveSessionStateLock:
    def test_critical_section_holds_the_lock_against_a_contender(self, tmp_path):
        state_path = tmp_path / "memory-recall-session.json"
        with memory_recall_debounce.exclusive_session_state_lock(state_path):
            contender = memory_recall_debounce.state_lock_path_for_session_state(
                state_path
            ).open("w")
            try:
                with pytest.raises(OSError):
                    fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
            finally:
                contender.close()

    def test_lock_is_released_after_the_critical_section(
        self, tmp_path, short_lock_timeout
    ):
        state_path = tmp_path / "memory-recall-session.json"
        with memory_recall_debounce.exclusive_session_state_lock(state_path):
            pass
        contender = memory_recall_debounce.state_lock_path_for_session_state(
            state_path
        ).open("w")
        assert memory_recall_debounce.acquire_exclusive_lock_before_deadline(contender)

    def test_lock_is_released_when_the_critical_section_raises(
        self, tmp_path, short_lock_timeout
    ):
        state_path = tmp_path / "memory-recall-session.json"
        with pytest.raises(SystemExit):
            with memory_recall_debounce.exclusive_session_state_lock(state_path):
                raise SystemExit(0)
        contender = memory_recall_debounce.state_lock_path_for_session_state(
            state_path
        ).open("w")
        assert memory_recall_debounce.acquire_exclusive_lock_before_deadline(contender)

    def test_contended_lock_still_runs_the_critical_section_unsynchronized(
        self, tmp_path, short_lock_timeout
    ):
        state_path = tmp_path / "memory-recall-session.json"
        holder = hold_lock_on_state(state_path)
        entered_critical_section = False
        try:
            with memory_recall_debounce.exclusive_session_state_lock(state_path):
                entered_critical_section = True
        finally:
            fcntl.flock(holder, fcntl.LOCK_UN)
            holder.close()
        assert entered_critical_section

    def test_unopenable_lock_path_still_runs_the_critical_section(
        self, tmp_path, short_lock_timeout
    ):
        unwritable_directory = tmp_path / "read-only"
        unwritable_directory.mkdir(mode=0o500)
        state_path = unwritable_directory / "memory-recall-session.json"
        entered_critical_section = False
        with memory_recall_debounce.exclusive_session_state_lock(state_path):
            entered_critical_section = True
        assert entered_critical_section


class TestWriteDebounceStateIsAtomic:
    def test_write_leaves_no_staging_file_behind(self, tmp_path):
        state_path = tmp_path / "memory-recall-session.json"
        memory_recall_debounce.write_debounce_state(
            state_path, {"recall_event_count": 3}
        )
        assert memory_recall_debounce.load_debounce_state(state_path) == {
            "recall_event_count": 3
        }
        assert list(tmp_path.glob("*.staging")) == []

    def test_failed_write_leaves_neither_staging_file_nor_state_file(self, tmp_path):
        unwritable_directory = tmp_path / "read-only"
        unwritable_directory.mkdir(mode=0o500)
        state_path = unwritable_directory / "memory-recall-session.json"
        memory_recall_debounce.write_debounce_state(
            state_path, {"recall_event_count": 3}
        )
        assert not state_path.exists()
        assert list(unwritable_directory.glob("*.staging")) == []
