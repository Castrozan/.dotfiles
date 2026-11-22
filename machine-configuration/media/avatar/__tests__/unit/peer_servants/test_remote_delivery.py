import shlex
from types import SimpleNamespace
from unittest.mock import Mock

import peer_sessions
import pytest
import wake_boundaries
from conversation_addressee import Addressee
from listener_session import ListenerPurpose
from voice_addressing import holds_the_floor
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


@pytest.mark.parametrize(
    ("variable", "hosts"),
    [(None, []), ("", []), ("  ", []), ("kira rin", ["kira", "rin"])],
)
def test_the_peers_are_the_hosts_named_in_the_environment(monkeypatch, variable, hosts):
    wake_boundaries.peers_of_this_machine.cache_clear()
    if variable is None:
        monkeypatch.delenv("AVATAR_PEER_HOSTS", raising=False)
    else:
        monkeypatch.setenv("AVATAR_PEER_HOSTS", variable)
    assert wake_boundaries.peers_of_this_machine().peer_hosts == hosts
    wake_boundaries.peers_of_this_machine.cache_clear()


def test_the_sessions_boundary_never_waits_on_a_peer(monkeypatch, ran):
    started = []
    peers = peer_sessions.PeerSessions(
        ["kira", "rin"], ran, start_worker=started.append
    )
    monkeypatch.setattr(wake_boundaries, "peers_of_this_machine", lambda: peers)
    monkeypatch.setattr(wake_boundaries, "live_sessions", lambda: [LOCAL_MEDEA])
    assert wake_boundaries.sessions_here_and_at_peers() == [LOCAL_MEDEA]
    ran.assert_not_called()
    ran.return_value = SimpleNamespace(
        returncode=0,
        stdout=peer_sessions.listing_of([LiveSession("Circe", "w2:p1")], None),
    )
    started.pop()()
    assert wake_boundaries.sessions_here_and_at_peers() == [
        LOCAL_MEDEA,
        LiveSession("Circe", "w2:p1", "kira"),
        LiveSession("Circe", "w2:p1", "rin"),
    ]


def test_the_remote_prompt_sends_every_avatar_command_to_the_room_machine(
    room_on_kira,
):
    text = spoken_prompt("check the build", None, REMOTE_MEDEA)
    assert "the room is on machine kira" in text
    for verb in ('say "..."', "follow", "close"):
        assert f"AVATAR_ROOM=kira avatar-talk {verb}" in text
    assert "ssh" not in text


def test_the_remote_meeting_prompt_also_names_the_room_in_every_command(room_on_kira):
    text = spoken_prompt("status", ListenerPurpose.MEETING, REMOTE_MEDEA)
    assert 'AVATAR_ROOM=kira avatar-talk say "..."' in text
    assert "AVATAR_ROOM=kira avatar-talk follow" in text
    assert "ssh" not in text


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
    assert "AVATAR_ROOM=kira avatar-talk say" in text


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
    holder = Addressee("w9:p4", "Medea", 3, held_host)
    assert holds_the_floor(holder, REMOTE_MEDEA) is holds


def test_the_same_pane_number_on_two_machines_is_two_sessions():
    holder = Addressee("w1:p1", "Medea", 3, "rin")
    assert not holds_the_floor(holder, LOCAL_MEDEA)
