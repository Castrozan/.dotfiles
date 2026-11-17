import shlex
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import wake_boundaries
import wake_listener
from conversation_addressee import Addressee
from listener_session import ListenerPurpose
from wake_fakes import armed_listener, boundaries
from wake_phrase import LiveSession
from wake_prompts import spoken_prompt

LOCAL_MEDEA = LiveSession("Medea", "w1:p1")
REMOTE_MEDEA = LiveSession("Medea", "w9:p4", "rin")
WORDS = "hey Medea, check the build"


@pytest.fixture
def ran(monkeypatch):
    runner = Mock(return_value=SimpleNamespace(returncode=0))
    monkeypatch.setattr(wake_boundaries.subprocess, "run", runner)
    return runner


@pytest.fixture
def room_on_kira(monkeypatch):
    monkeypatch.setenv("AVATAR_AGENT_HOST", "kira")


def test_a_local_session_is_prompted_without_ssh(ran):
    assert wake_boundaries.prompt_now("w1:p1", "go")
    assert ran.call_args.args[0] == ["herdr", "agent", "prompt", "w1:p1", "go"]


def test_a_remote_session_is_prompted_through_ssh_with_the_command_quoted(ran):
    wake_boundaries.prompt_now("w9:p4", "it's $HOME; go", "rin")
    command = ran.call_args.args[0]
    assert command[:-1] == [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        "rin",
    ]
    assert shlex.split(command[-1]) == [
        "herdr",
        "agent",
        "prompt",
        "w9:p4",
        "it's $HOME; go",
    ]
    assert ran.call_args.kwargs["timeout"] == wake_boundaries.COMMAND_TIMEOUT_SECONDS


def test_a_remote_session_is_notified_at_idle_through_ssh(ran):
    wake_boundaries.notify_at_idle("w9:p4", "go", "rin")
    command = ran.call_args.args[0]
    assert command[-2] == "rin"
    assert shlex.split(command[-1]) == [
        "a2a",
        "notify",
        "--sender",
        "voice",
        "w9:p4",
        "go",
    ]


def test_the_sessions_boundary_lists_the_peers_named_in_the_environment(
    monkeypatch, ran
):
    monkeypatch.setenv("AVATAR_PEER_HOSTS", "kira rin")
    monkeypatch.setattr(wake_boundaries, "live_sessions", lambda: [LOCAL_MEDEA])
    ran.return_value = SimpleNamespace(returncode=255, stdout="")
    assert wake_boundaries.sessions_here_and_at_peers() == [LOCAL_MEDEA]
    assert sorted(call.args[0][-3] for call in ran.call_args_list) == ["kira", "rin"]


@pytest.mark.parametrize("peers", [None, "", "  "])
def test_no_peer_hosts_means_no_ssh(monkeypatch, ran, peers):
    if peers is None:
        monkeypatch.delenv("AVATAR_PEER_HOSTS", raising=False)
    else:
        monkeypatch.setenv("AVATAR_PEER_HOSTS", peers)
    monkeypatch.setattr(wake_boundaries, "live_sessions", lambda: [LOCAL_MEDEA])
    assert wake_boundaries.sessions_here_and_at_peers() == [LOCAL_MEDEA]
    ran.assert_not_called()


def test_the_remote_prompt_sends_every_avatar_command_to_the_room_machine(
    room_on_kira,
):
    text = spoken_prompt("check the build", None, REMOTE_MEDEA)
    assert "the room is on machine kira" in text
    for verb in ('say "..."', "follow", "close"):
        assert f"ssh kira HERDR_PANE_ID=w9:p4 avatar-talk {verb}" in text


def test_the_remote_meeting_prompt_also_runs_its_commands_in_the_room(room_on_kira):
    text = spoken_prompt("status", ListenerPurpose.MEETING, REMOTE_MEDEA)
    assert "ssh kira HERDR_PANE_ID=w9:p4 avatar-command speak" in text
    assert "ssh kira HERDR_PANE_ID=w9:p4 avatar-listen follow" in text


@pytest.mark.parametrize("session", [None, LOCAL_MEDEA])
def test_a_same_machine_prompt_is_unchanged(session):
    assert spoken_prompt("check the build", None, session) == (
        "[wake] Voice from the room, speaker not verified: check the build "
        "An avatar conversation is opening: speak with avatar-talk say, and hear "
        "the reply through avatar-talk follow in a background watcher. When the "
        "room dismisses you, such as 'you can go now', say a short goodbye and run "
        "avatar-talk close, which hands the room back to the wake."
    )


def test_waking_a_remote_session_prompts_it_on_its_host(room_on_kira):
    fakes = boundaries(heard=WORDS, sessions=(REMOTE_MEDEA,))
    armed_listener(fakes).hear(b"segment")
    pane, text, host = fakes.prompt_now.call_args.args
    assert (pane, host) == ("w9:p4", "rin")
    assert "ssh kira HERDR_PANE_ID=w9:p4 avatar-talk say" in text


def test_a_refused_remote_prompt_is_notified_at_idle_on_its_host(room_on_kira):
    fakes = boundaries(
        heard=WORDS,
        sessions=(REMOTE_MEDEA,),
        prompt_now=Mock(return_value=False),
    )
    armed_listener(fakes).hear(b"segment")
    assert fakes.notify_at_idle.call_args.args[::2] == ("w9:p4", "rin")


def test_waking_a_remote_session_hands_it_the_room_with_its_host(room_on_kira):
    fakes = boundaries(heard=WORDS, sessions=(REMOTE_MEDEA,))
    armed_listener(fakes).hear(b"segment")
    assert fakes.hand_to.call_args.args[0] == Addressee("w9:p4", "Medea", 0, "rin")


def test_waking_a_local_session_hands_it_the_room_without_a_host():
    fakes = boundaries(heard=WORDS, sessions=(LOCAL_MEDEA,))
    armed_listener(fakes).hear(b"segment")
    assert fakes.hand_to.call_args.args[0] == Addressee("w1:p1", "Medea", 0, None)


@pytest.mark.parametrize(
    ("held_host", "holds"), [("rin", True), (None, False), ("kira", False)]
)
def test_the_floor_is_held_only_by_the_same_pane_on_the_same_host(held_host, holds):
    fakes = boundaries(
        addressee=Mock(return_value=Addressee("w9:p4", "Medea", 3, held_host))
    )
    listener = wake_listener.WakeListener(fakes, dry_run=False)
    match = SimpleNamespace(session=REMOTE_MEDEA)
    assert listener.already_holds_the_floor(match) is holds


def test_the_same_pane_number_on_two_machines_is_two_sessions():
    fakes = boundaries(
        addressee=Mock(return_value=Addressee("w1:p1", "Medea", 3, "rin"))
    )
    listener = wake_listener.WakeListener(fakes, dry_run=False)
    assert not listener.already_holds_the_floor(SimpleNamespace(session=LOCAL_MEDEA))
