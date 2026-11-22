import contextlib
import pathlib
import re
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import mac_listen
import mac_meeting
import mac_meeting_cli
import mac_talk
import pytest
from conversation_state import ConversationPhase

AVATAR = pathlib.Path(__file__).resolve().parents[3]
MAC_MODULES = [
    "mac_meeting.py",
    "mac_meeting_cli.py",
    "mac_listen.py",
    "mac_call_relay.py",
    "mac_call_capture.py",
]
MAC_CONVERSATION = AVATAR / "scripts/conversation/mac_conversation"
FORBIDDEN_REACH = re.compile(r"\bssh\b|remote_agent|remote_meeting|remote_talk")


@pytest.fixture
def meeting_steps(monkeypatch, tmp_path):
    steps = Mock()
    directory = tmp_path / "runtime"
    monkeypatch.setattr(
        mac_meeting_cli.listener_runtime, "runtime_directory", lambda: directory
    )
    monkeypatch.setattr(
        mac_meeting_cli,
        "MEETING_STEPS",
        {"start": steps.start, "stop": steps.stop, "controls": steps.controls},
    )
    steps.directory = directory
    return steps


def run_cli(monkeypatch, *arguments):
    monkeypatch.setattr(mac_meeting_cli.sys, "argv", ["avatar-meeting", *arguments])
    with pytest.raises(SystemExit) as finished:
        mac_meeting_cli.main()
    return finished.value.code


@pytest.mark.parametrize("verb", ["start", "stop", "controls"])
def test_each_verb_runs_its_local_step_in_the_runtime_directory(
    monkeypatch, meeting_steps, verb
):
    assert run_cli(monkeypatch, verb) == 0
    getattr(meeting_steps, verb).assert_called_once_with(meeting_steps.directory)


@pytest.mark.parametrize(
    "arguments", [[], ["fly"], ["start", "now"], ["stop", "now"], ["listen"]]
)
def test_anything_else_is_a_usage_error_that_runs_nothing(
    monkeypatch, meeting_steps, capsys, arguments
):
    assert run_cli(monkeypatch, *arguments) == 1
    assert "Usage: avatar-start | avatar-stop" in capsys.readouterr().err
    assert meeting_steps.mock_calls == []


@pytest.mark.parametrize(
    "failure",
    [
        RuntimeError("no meeting"),
        TimeoutError("no page"),
        OSError("no OBS"),
        subprocess.TimeoutExpired("open", 1),
    ],
)
def test_a_failed_step_ends_with_its_reason_and_a_failing_exit(
    monkeypatch, meeting_steps, capsys, failure
):
    meeting_steps.start.side_effect = failure
    assert run_cli(monkeypatch, "start") == 1
    assert str(failure) in capsys.readouterr().err


def test_listening_starts_the_local_meeting_listener_with_the_language(
    monkeypatch, tmp_path
):
    listened = Mock()
    monkeypatch.setattr(mac_listen.mac_meeting, "listen_to_the_call", listened)
    monkeypatch.setattr(
        mac_listen.listener_runtime, "runtime_directory", lambda: tmp_path
    )
    monkeypatch.setattr(
        mac_listen.sys, "argv", ["avatar-listen", "start", "--language", "pt"]
    )
    mac_listen.main()
    listened.assert_called_once_with(tmp_path, "pt")


def test_a_refused_listening_start_ends_with_the_reason(monkeypatch, capsys):
    monkeypatch.setattr(
        mac_listen.mac_meeting,
        "listen_to_the_call",
        Mock(side_effect=RuntimeError(mac_meeting.CONVERSATION_OPEN)),
    )
    monkeypatch.setattr(mac_listen.sys, "argv", ["avatar-listen", "start"])
    with pytest.raises(SystemExit) as finished:
        mac_listen.main()
    assert finished.value.code == 1
    assert "avatar-talk close" in capsys.readouterr().err


@pytest.mark.parametrize("verb", ["read", "follow", "stop", "status", "voices"])
def test_every_other_listen_verb_runs_the_shared_listen_command_here(monkeypatch, verb):
    shared = Mock()
    monkeypatch.setattr(mac_listen.listen_cli, "main", shared)
    monkeypatch.setattr(mac_listen.sys, "argv", ["avatar-listen", verb])
    mac_listen.main()
    shared.assert_called_once_with()


@pytest.fixture
def this_mac_in(monkeypatch, tmp_path):
    mac = SimpleNamespace(phase=ConversationPhase.MEETING, stage=Mock(), begin=Mock())
    mac.stage.standing = contextlib.nullcontext
    monkeypatch.delenv("HERDR_PANE_ID", raising=False)
    monkeypatch.delenv("AVATAR_ROOM", raising=False)
    monkeypatch.setattr(
        mac_talk.listener_runtime, "runtime_directory", lambda: tmp_path / "runtime"
    )
    monkeypatch.setattr(mac_talk, "mac_stage", mac.stage)
    monkeypatch.setattr(mac_talk.mac_turns, "mac_stage", mac.stage)
    monkeypatch.setattr(mac_talk.local_seat, "health", lambda: None)
    monkeypatch.setattr(mac_talk.listener_session, "begin_listening", mac.begin)
    monkeypatch.setattr(mac_talk.conversation_state, "observe", lambda _: mac.phase)
    return mac


@pytest.mark.parametrize("arguments", [["open"], ["open", "--live"], ["close"]])
def test_a_conversation_does_not_open_while_a_meeting_runs_on_this_mac(
    this_mac_in, arguments
):
    with pytest.raises(RuntimeError, match="avatar-stop"):
        mac_talk.carry_out(arguments)
    assert this_mac_in.stage.mock_calls == []
    assert not this_mac_in.begin.called


def test_speech_in_a_meeting_plays_through_the_stage_and_so_the_seat_page(
    this_mac_in,
):
    assert mac_talk.carry_out(["say", "Good evening", "happy"]) == 0
    this_mac_in.stage.speak.assert_called_once_with("Good evening", "happy", None)


@pytest.mark.parametrize("module", MAC_MODULES)
def test_no_mac_meeting_module_reaches_the_avatar_host(module):
    assert not FORBIDDEN_REACH.search((MAC_CONVERSATION / module).read_text())


def test_the_mac_meeting_commands_are_the_local_modules_and_nothing_forwards_them():
    commands = (AVATAR / "avatar-remote-home-manager.nix").read_text()
    packages = commands[commands.index("home.packages") :]
    assert "remoteMeeting" not in commands
    for name, entry in [
        ("avatar-start", "mac_meeting_cli.py start"),
        ("avatar-stop", "mac_meeting_cli.py stop"),
        ("avatar-controls", "mac_meeting_cli.py controls"),
        ("avatar-listen", "mac_listen.py"),
    ]:
        assert f'conversation.meetingCommand "{name}" "{entry}"' in packages
        assert f'forwardToHost "{name}"' not in packages
