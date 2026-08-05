from agent_session import restart_lock


def test_restart_lock_blocks_a_second_relaunch_for_the_same_process(
    monkeypatch, tmp_path
):
    lock_path = tmp_path / "agent-session-restart-102.lock"
    monkeypatch.setattr(
        restart_lock, "restart_lock_path_for", lambda _process_identifier: lock_path
    )

    first_restart_lock = restart_lock.acquire_restart_lock(102)

    assert first_restart_lock is not None
    assert first_restart_lock.path == lock_path
    assert restart_lock.acquire_restart_lock(102) is None

    restart_lock.release_restart_lock(first_restart_lock)

    second_restart_lock = restart_lock.acquire_restart_lock(102)

    assert second_restart_lock is not None
    assert second_restart_lock.path == lock_path


def test_releasing_an_expired_restart_lock_does_not_remove_its_replacement(
    monkeypatch, tmp_path
):
    lock_path = tmp_path / "agent-session-restart-102.lock"
    monkeypatch.setattr(
        restart_lock, "restart_lock_path_for", lambda _process_identifier: lock_path
    )
    first_restart_lock = restart_lock.acquire_restart_lock(102)

    assert first_restart_lock is not None
    monkeypatch.setattr(
        restart_lock.time,
        "time",
        lambda: lock_path.stat().st_mtime + restart_lock.RESTART_LOCK_STALE_SECONDS + 1,
    )

    replacement_restart_lock = restart_lock.acquire_restart_lock(102)

    assert replacement_restart_lock is not None
    assert replacement_restart_lock.owner_token != first_restart_lock.owner_token

    restart_lock.release_restart_lock(first_restart_lock)

    assert lock_path.exists()
