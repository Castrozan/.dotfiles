import json
import sys
from unittest.mock import Mock
from concurrent.futures import ThreadPoolExecutor

import listener_runtime
import pytest
import wake_claim
import wake_listener
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

PANES = st.text(
    st.characters(blacklist_characters="\x00", blacklist_categories=["Cs"]),
    min_size=1,
    max_size=12,
)
ROOMS = st.sampled_from(["kira", "chise"])
OFFSETS_WITHIN_THE_WINDOW = st.lists(
    st.tuples(
        ROOMS,
        st.integers(0, wake_claim.CLAIM_SECONDS * 1000 - 1).map(
            lambda milliseconds: milliseconds / 1000
        ),
    ),
    min_size=1,
    max_size=8,
)
START = 1_000_000.0
NO_FIXTURE_CHECK = settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=60
)


@pytest.fixture(autouse=True)
def no_active_conversation(monkeypatch):
    monkeypatch.setenv("AVATAR_AGENT_HOST", "chise")
    monkeypatch.setattr(wake_claim, "active_conversation", Mock(return_value=None))
    monkeypatch.setattr(wake_claim, "conversation_in_room", Mock(return_value=None))


def claims_in_time_order(directory, pane, first_room, attempts):
    results = [(first_room, wake_claim.claim(directory, pane, first_room, START))]
    for room, offset in sorted(attempts, key=lambda attempt: attempt[1]):
        results.append((room, wake_claim.claim(directory, pane, room, START + offset)))
    return results


@NO_FIXTURE_CHECK
@given(pane=PANES, first_room=ROOMS, attempts=OFFSETS_WITHIN_THE_WINDOW)
def test_within_the_window_only_the_first_room_ever_wins(
    tmp_path_factory, pane, first_room, attempts
):
    directory = tmp_path_factory.mktemp("claims")
    results = claims_in_time_order(directory, pane, first_room, attempts)
    assert {room for room, won in results if won} == {first_room}
    assert all(won for room, won in results if room == first_room)


@NO_FIXTURE_CHECK
@given(
    pane=PANES,
    first_room=ROOMS,
    waited=st.floats(wake_claim.CLAIM_SECONDS, 10_000),
)
def test_after_the_window_the_other_room_may_win(
    tmp_path_factory, pane, first_room, waited
):
    directory = tmp_path_factory.mktemp("claims")
    other_room = "chise" if first_room == "kira" else "kira"
    assert wake_claim.claim(directory, pane, first_room, START)
    assert wake_claim.claim(directory, pane, other_room, START + waited)
    assert not wake_claim.claim(directory, pane, first_room, START + waited + 1)


@NO_FIXTURE_CHECK
@given(
    pane=PANES,
    room=ROOMS,
    spacings=st.lists(st.floats(0, 10_000), min_size=1, max_size=6),
)
def test_the_same_room_claims_again_at_any_time(tmp_path_factory, pane, room, spacings):
    directory = tmp_path_factory.mktemp("claims")
    moment = START
    assert wake_claim.claim(directory, pane, room, moment)
    for spacing in spacings:
        moment += spacing
        assert wake_claim.claim(directory, pane, room, moment)


def test_each_pane_has_its_own_claim_file(tmp_path):
    assert wake_claim.claim(tmp_path, "w1:p1", "kira", START)
    assert wake_claim.claim(tmp_path, "w1:p2", "chise", START)
    assert not wake_claim.claim(tmp_path, "w1:p1", "chise", START)
    names = sorted(path.name for path in (tmp_path / "wake-claims").iterdir())
    assert len(names) == 2 and all(
        "/" not in name and ":" not in name for name in names
    )


def test_panes_that_look_alike_once_sanitized_keep_separate_claims(tmp_path):
    assert wake_claim.claim(tmp_path, "w1:p1", "kira", START)
    assert wake_claim.claim(tmp_path, "w1_p1", "chise", START)
    assert wake_claim.claim(tmp_path, "..", "chise", START)


def test_a_claim_file_holds_the_room_and_the_exact_claim_time(tmp_path):
    wake_claim.claim(tmp_path, "w1:p1", "kira", START)
    (path,) = (tmp_path / "wake-claims").iterdir()
    assert json.loads(path.read_text()) == {"room": "kira", "claimed_at": START}


def test_simultaneous_claimants_leave_exactly_one_winning_room(tmp_path):
    rooms = ["kira", "chise"] * 8
    with ThreadPoolExecutor(max_workers=len(rooms)) as pool:
        outcomes = list(
            pool.map(
                lambda room: (room, wake_claim.claim(tmp_path, "w:p", room, START)),
                rooms,
            )
        )
    assert len({room for room, won in outcomes if won}) == 1


@pytest.fixture
def runtime_in(monkeypatch, tmp_path):
    monkeypatch.setattr(listener_runtime, "runtime_directory", lambda: tmp_path)
    return tmp_path


def run_the_wake(monkeypatch, *arguments):
    monkeypatch.setattr(sys, "argv", ["avatar-wake", *arguments])
    monkeypatch.setattr(
        wake_listener, "run", lambda wake: pytest.fail("the claim must not listen")
    )
    with pytest.raises(SystemExit) as stopped:
        wake_listener.main()
    return stopped.value.code


def test_the_claim_flag_exits_zero_for_the_winner_and_one_for_the_loser(
    monkeypatch, runtime_in
):
    assert run_the_wake(monkeypatch, "--claim", "w1:p1", "--room", "kira") == 0
    assert run_the_wake(monkeypatch, "--claim", "w1:p1", "--room", "chise") == 1
    assert run_the_wake(monkeypatch, "--claim", "w1:p1", "--room", "kira") == 0


def test_the_claim_flag_without_a_room_is_a_usage_error(monkeypatch, runtime_in):
    assert run_the_wake(monkeypatch, "--claim", "w1:p1") == wake_claim.USAGE_ERROR
    assert not (runtime_in / "wake-claims").exists()
