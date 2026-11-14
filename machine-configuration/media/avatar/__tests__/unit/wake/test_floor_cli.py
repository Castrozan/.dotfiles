import fcntl
import tempfile
from pathlib import Path

import conversation_addressee
import floor_cli
import listener_runtime
import pytest
from floor_runner import run_floor_cli
import remote_agent
import speaking_floor
from conversation_addressee import Addressee
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from remote_agent import AgentPane
from wake_phrase import LiveSession

NAMES = st.text(alphabet="abcdefg", min_size=1, max_size=4)
PANES = st.sampled_from(["wW:pPA", "wW:pPB", "wX:pPA"])
REPEATED_SETUP_IS_IDEMPOTENT = settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)


def test_an_agent_with_a_servant_is_handed_the_floor_with_its_host(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(remote_agent, "servant_at", lambda agent: "Voyager")
    assert run_floor_cli(monkeypatch, tmp_path, "--agent", "kira:wW:pPZ") == 0
    assert conversation_addressee.current(tmp_path) == Addressee(
        "wW:pPZ", "Voyager", 0, "kira"
    )


def test_an_agent_pane_without_a_servant_fails_and_leaves_the_floor(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(remote_agent, "servant_at", lambda agent: None)
    assert run_floor_cli(monkeypatch, tmp_path, "--agent", "kira:wW:pPZ") == 1
    assert floor_cli.NO_SERVANT_MESSAGE in capsys.readouterr().err
    assert conversation_addressee.current(tmp_path) is None


def test_an_unreadable_remote_session_fails_with_its_reason(
    monkeypatch, tmp_path, capsys
):
    def unreachable(agent):
        raise OSError("ssh is missing")

    monkeypatch.setattr(remote_agent, "servant_at", unreachable)
    assert run_floor_cli(monkeypatch, tmp_path, "--agent", "kira:wW:pPZ") == 1
    assert "ssh is missing" in capsys.readouterr().err


@pytest.mark.parametrize("agent", ["kira", ":wW:pPZ", "kira:"])
def test_an_agent_that_is_not_host_and_pane_is_refused(monkeypatch, tmp_path, agent):
    assert run_floor_cli(monkeypatch, tmp_path, "--agent", agent) == 2


def test_the_shared_hand_over_names_the_servant_and_reports_whether_it_exists(
    monkeypatch, tmp_path
):
    agent = AgentPane("kira", "wW:pPZ")
    monkeypatch.setattr(remote_agent, "servant_at", lambda pane: None)
    assert speaking_floor.hand_to_remote_agent(tmp_path, agent) is False
    monkeypatch.setattr(remote_agent, "servant_at", lambda pane: "Voyager")
    assert speaking_floor.hand_to_remote_agent(tmp_path, agent) is True
    assert conversation_addressee.current(tmp_path).host == "kira"


def test_without_an_agent_a_pane_outside_herdr_claims_nothing(monkeypatch, tmp_path):
    monkeypatch.delenv(floor_cli.PANE_ENVIRONMENT_VARIABLE, raising=False)
    assert run_floor_cli(monkeypatch, tmp_path) == 0
    assert conversation_addressee.current(tmp_path) is None


def run_in_fresh_directory(monkeypatch, *arguments):
    with tempfile.TemporaryDirectory() as directory:
        code = run_floor_cli(monkeypatch, Path(directory), *arguments)
        return code, conversation_addressee.current(Path(directory))


def speak_from_pane(monkeypatch, tmp_path, pane, sessions, listening=False):
    monkeypatch.setenv(floor_cli.PANE_ENVIRONMENT_VARIABLE, pane)
    monkeypatch.setattr(floor_cli, "live_sessions", lambda: sessions)
    monkeypatch.setattr(listener_runtime, "listening", lambda: listening)
    return run_floor_cli(monkeypatch, tmp_path)


@REPEATED_SETUP_IS_IDEMPOTENT
@given(
    panes=st.lists(PANES, unique=True, max_size=3),
    servants=st.lists(NAMES, min_size=3, max_size=3),
    pane=PANES,
)
def test_a_speaking_pane_shows_the_character_of_its_own_servant_only(
    shown, monkeypatch, panes, servants, pane
):
    sessions = [
        LiveSession(servant=servant, pane=session_pane)
        for session_pane, servant in zip(panes, servants, strict=False)
    ]
    shown.clear()
    with tempfile.TemporaryDirectory() as directory:
        speak_from_pane(monkeypatch, Path(directory), pane, sessions)
    expected = [session.servant for session in sessions if session.pane == pane]
    assert shown == expected


def test_the_holder_speaking_again_shows_its_character(shown, monkeypatch, tmp_path):
    conversation_addressee.hand_to(tmp_path, Addressee("wW:pPA", "Circe", 3))
    assert speak_from_pane(monkeypatch, tmp_path, "wW:pPA", [], listening=True) == 0
    assert shown == ["Circe"]


def test_a_pane_that_does_not_hold_the_floor_is_refused_and_shows_nothing(
    shown, monkeypatch, tmp_path, capsys
):
    conversation_addressee.hand_to(tmp_path, Addressee("wW:pPA", "Circe", 3))
    sessions = [LiveSession("Circe", "wW:pPA"), LiveSession("Medea", "wW:pPB")]
    assert speak_from_pane(monkeypatch, tmp_path, "wW:pPB", sessions, True) == 1
    assert "Circe holds the avatar's floor" in capsys.readouterr().err
    assert shown == []


def test_the_character_is_shown_after_the_addressee_lock_is_released(
    monkeypatch, tmp_path
):
    lock_was_free = []

    def show_while_checking_the_lock(servant):
        with open(tmp_path / conversation_addressee.LOCK_FILE) as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                lock_was_free.append(True)
            except BlockingIOError:
                lock_was_free.append(False)

    monkeypatch.setattr(
        floor_cli.servant_character, "show_for", show_while_checking_the_lock
    )
    sessions = [LiveSession("Medea", "wW:pPB")]
    speak_from_pane(monkeypatch, tmp_path, "wW:pPB", sessions, listening=True)
    assert conversation_addressee.current(tmp_path).servant == "Medea"
    assert lock_was_free == [True]


@REPEATED_SETUP_IS_IDEMPOTENT
@given(heard_through=st.integers(min_value=0, max_value=10**6))
def test_an_agent_handover_carries_the_position_heard_through(
    monkeypatch, heard_through
):
    monkeypatch.setattr(remote_agent, "servant_at", lambda agent: "Voyager")
    monkeypatch.setattr(floor_cli.servant_character, "show_for", lambda servant: None)
    code, addressee = run_in_fresh_directory(
        monkeypatch, "--agent", "kira:wW:pPZ", "--heard-through", str(heard_through)
    )
    assert code == 0
    assert addressee == Addressee("wW:pPZ", "Voyager", heard_through, "kira")


@pytest.mark.parametrize(
    "arguments",
    [
        ["--heard-through", "4"],
        ["--speaker", "kira:wW:pPZ", "--heard-through", "4"],
        ["--speaker", "kira:wW:pPZ", "--agent", "kira:wW:pPZ"],
    ],
)
def test_the_options_that_do_not_belong_together_are_refused(
    monkeypatch, tmp_path, arguments
):
    assert run_floor_cli(monkeypatch, tmp_path, *arguments) == 2
