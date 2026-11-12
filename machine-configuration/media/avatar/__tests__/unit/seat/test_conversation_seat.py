import argparse
import json
from unittest.mock import Mock

import conversation_effects
import conversation_seat
import listener_runtime
import listener_session
import pytest
import start
from conversation_seat import Seat


def write_listener(directory, **configuration):
    (directory / "listener.json").write_text(
        json.dumps({"purpose": "conversation", **configuration})
    )


def open_seated(tmp_path, monkeypatch, seat):
    monkeypatch.setattr(listener_runtime, "listening", lambda: False)
    monkeypatch.setattr(start, "bring_up", Mock())
    monkeypatch.setattr(conversation_effects.subprocess, "run", Mock())
    begin = Mock()
    monkeypatch.setattr(listener_session, "begin_listening", begin)
    conversation_effects.open_conversation(
        argparse.Namespace(language="pt", character=None, seat=seat), tmp_path
    )
    return begin


def test_a_remote_seat_starts_its_bridge_and_listens_to_the_remote_microphone(
    tmp_path, monkeypatch
):
    systemctl = Mock()
    monkeypatch.setattr(listener_session, "systemctl", systemctl)
    monkeypatch.setattr(conversation_seat, "remote_seat_listening", lambda: True)
    begin = open_seated(tmp_path, monkeypatch, "remote")
    systemctl.assert_called_once_with("start", conversation_seat.REMOTE_SEAT_SERVICE)
    assert begin.call_args.args[2] == {"human": "AvatarRemoteMicrophone.monitor"}
    assert begin.call_args.kwargs["seat"] is Seat.REMOTE


def test_the_room_seat_starts_no_bridge(tmp_path, monkeypatch):
    systemctl = Mock()
    monkeypatch.setattr(listener_session, "systemctl", systemctl)
    begin = open_seated(tmp_path, monkeypatch, "room")
    systemctl.assert_not_called()
    assert begin.call_args.args[2] == {"human": "AvatarRoomMicrophone"}


def test_a_bridge_that_never_listens_fails_the_open_and_closes_it(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(listener_session, "systemctl", Mock())
    monkeypatch.setattr(conversation_seat, "remote_seat_listening", lambda: False)
    monkeypatch.setattr(conversation_seat, "REMOTE_SEAT_WAIT_SECONDS", 0)
    monkeypatch.setattr(conversation_seat, "POLL_SECONDS", 0)
    close = Mock()
    monkeypatch.setattr(conversation_effects, "close_conversation", close)
    with pytest.raises(TimeoutError):
        open_seated(tmp_path, monkeypatch, "remote")
    close.assert_called_once()


@pytest.mark.parametrize(
    ("listening", "configuration", "seat"),
    [
        (True, {"seat": "remote"}, Seat.REMOTE),
        (True, {"seat": "room"}, Seat.ROOM),
        (True, {}, Seat.ROOM),
        (False, {"seat": "remote"}, Seat.ROOM),
    ],
)
def test_the_seat_is_remote_only_while_a_remote_conversation_listens(
    tmp_path, monkeypatch, listening, configuration, seat
):
    monkeypatch.setattr(listener_runtime, "listening", lambda: listening)
    write_listener(tmp_path, **configuration)
    assert conversation_seat.current(tmp_path) is seat


def test_every_seat_has_a_microphone_and_a_speech_output():
    assert set(conversation_seat.MICROPHONE_BY_SEAT) == set(Seat)
    assert set(conversation_seat.SPEECH_OUTPUT_BY_SEAT) == set(Seat)
