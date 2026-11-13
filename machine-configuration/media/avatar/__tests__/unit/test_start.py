import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from conversation_seat import Seat


spec = importlib.util.spec_from_file_location(
    "avatar_start", Path(__file__).resolve().parents[2] / "scripts/start.py"
)
start = importlib.util.module_from_spec(spec)
spec.loader.exec_module(start)


def test_start_recovers_a_missing_graph_before_claiming_readiness(monkeypatch):
    runner = Mock()
    monkeypatch.setattr(start.subprocess, "run", runner)
    monkeypatch.setattr(start, "audio_ready", Mock(side_effect=[False, True]))
    monkeypatch.setattr(start, "wait_until_ready", Mock())
    start.main()
    assert [call.args[0] for call in runner.call_args_list] == [
        ["avatar-audio", "start"],
        ["systemctl", "--user", "start", "avatar.target"],
        ["avatar-audio", "open"],
    ]


def test_healthy_start_preserves_the_running_runtime(monkeypatch):
    runner = Mock()
    monkeypatch.setattr(start.subprocess, "run", runner)
    monkeypatch.setattr(start, "audio_ready", Mock(return_value=True))
    monkeypatch.setattr(start, "wait_until_ready", Mock())
    start.main()
    assert runner.call_args_list[0].args[0] == [
        "systemctl",
        "--user",
        "start",
        "avatar.target",
    ]
    assert runner.call_args_list[1].args[0] == ["avatar-audio", "open"]
    assert runner.call_count == 2


def test_a_target_is_ready_only_when_all_of_its_own_checks_pass(monkeypatch):
    monkeypatch.setattr(start, "service_failed", lambda units: False)
    monkeypatch.setattr(start.time, "sleep", Mock())
    answers = iter([False, True])
    start.wait_until_ready(
        start.TARGET_UNITS[start.MEETING_TARGET], (lambda: next(answers), lambda: True)
    )


def test_a_failed_bring_up_stops_only_the_requested_target(monkeypatch):
    runner = Mock()
    monkeypatch.setattr(start.subprocess, "run", runner)
    monkeypatch.setattr(start, "audio_ready", Mock(return_value=True))
    monkeypatch.setattr(start, "wait_until_ready", Mock(side_effect=TimeoutError))
    try:
        start.bring_up("avatar-conversation.target", ())
    except TimeoutError:
        pass
    assert runner.call_args_list[-1].args[0] == [
        "systemctl",
        "--user",
        "stop",
        "avatar-conversation.target",
    ]


def test_a_failed_camera_does_not_block_the_conversation_target(monkeypatch):
    queried_units = []

    def fake_is_failed(command, **_):
        units = command[3:]
        queried_units.append(units)
        return SimpleNamespace(
            stdout="\n".join(
                "failed" if unit == "avatar-camera" else "active" for unit in units
            )
        )

    monkeypatch.setattr(start.subprocess, "run", fake_is_failed)
    monkeypatch.setattr(start.time, "sleep", Mock())
    start.wait_until_ready(
        start.TARGET_UNITS[start.CONVERSATION_TARGET], (lambda: True,)
    )
    assert queried_units == [list(start.TARGET_UNITS[start.CONVERSATION_TARGET])]
    assert "avatar-camera" not in queried_units[0]
    with pytest.raises(RuntimeError):
        start.wait_until_ready(
            start.TARGET_UNITS[start.MEETING_TARGET], (lambda: True,)
        )


def test_a_conversation_bring_up_never_stops_the_meeting_target(monkeypatch):
    runner = Mock()
    monkeypatch.setattr(start.subprocess, "run", runner)
    monkeypatch.setattr(start, "audio_ready", Mock(side_effect=[False, True]))
    monkeypatch.setattr(start, "wait_until_ready", Mock())
    start.bring_up(start.CONVERSATION_TARGET, ())
    assert [call.args[0] for call in runner.call_args_list] == [
        ["avatar-audio", "start"],
        ["systemctl", "--user", "start", "avatar-conversation.target"],
    ]
    assert ["systemctl", "--user", "stop", "avatar.target"] not in [
        call.args[0] for call in runner.call_args_list
    ]


def test_audio_readiness_requires_a_running_owned_graph(monkeypatch):
    runner = Mock(
        return_value=SimpleNamespace(
            returncode=0, stdout=json.dumps({"running": False})
        )
    )
    monkeypatch.setattr(start.subprocess, "run", runner)
    assert start.audio_ready() is False
    runner.return_value = SimpleNamespace(
        returncode=0, stdout=json.dumps({"running": True})
    )
    assert start.audio_ready() is True


def test_the_seat_defaults_to_the_room():
    assert start.parse_seat([]) is Seat.ROOM
    assert start.parse_seat(["--seat", "room"]) is Seat.ROOM
    assert start.parse_seat(["--seat", "remote"]) is Seat.REMOTE


def test_an_unknown_seat_is_refused():
    with pytest.raises(SystemExit):
        start.parse_seat(["--seat", "lounge"])


def test_the_room_start_prepares_no_seat_and_keeps_its_ready_line(monkeypatch, capsys):
    monkeypatch.setattr(start.subprocess, "run", Mock())
    monkeypatch.setattr(start, "audio_ready", Mock(return_value=True))
    monkeypatch.setattr(start, "wait_until_ready", Mock())
    prepare = Mock()
    monkeypatch.setattr(start.conversation_seat, "prepare", prepare)
    start.main()
    prepare.assert_not_called()
    assert capsys.readouterr().out == (
        "Avatar ready with her voice and the default microphone open. Check levels "
        "with avatar-audio status. Switch video with avatar-command mode\n"
    )


def test_the_remote_start_opens_both_call_channels_but_never_the_room_microphone(
    monkeypatch, capsys
):
    order = []
    monkeypatch.setattr(
        start.subprocess, "run", lambda command, **_: order.append(command)
    )
    monkeypatch.setattr(start, "audio_ready", Mock(return_value=True))
    monkeypatch.setattr(start, "wait_until_ready", Mock())
    monkeypatch.setattr(
        start.conversation_seat, "prepare", lambda seat: order.append(("prepare", seat))
    )
    start.main(Seat.REMOTE)
    assert order == [
        ["systemctl", "--user", "start", "avatar.target"],
        ("prepare", Seat.REMOTE),
        ["avatar-audio", "mute", "agent", "0"],
        ["avatar-audio", "mute", "human", "0"],
    ]
    assert "voice and the microphone at the remote seat" in capsys.readouterr().out


def test_a_remote_start_whose_seat_never_listens_fails_without_claiming_ready(
    monkeypatch, capsys
):
    monkeypatch.setattr(start.subprocess, "run", Mock())
    monkeypatch.setattr(start, "audio_ready", Mock(return_value=True))
    monkeypatch.setattr(start, "wait_until_ready", Mock())
    monkeypatch.setattr(
        start.conversation_seat, "prepare", Mock(side_effect=TimeoutError("no seat"))
    )
    with pytest.raises(TimeoutError):
        start.main(Seat.REMOTE)
    assert capsys.readouterr().out == ""
