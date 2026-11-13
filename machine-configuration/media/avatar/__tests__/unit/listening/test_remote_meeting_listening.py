import json
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import conversation_seat
import conversation_state
import listen_cli
import listener_session
import pytest
from conversation_seat import Seat
from conversation_state import ConversationPhase


@pytest.fixture
def begin(monkeypatch):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.CLOSED
    )
    begin = Mock()
    monkeypatch.setattr(listener_session, "begin_listening", begin)
    monkeypatch.setattr(
        listen_cli,
        "default_microphone",
        Mock(side_effect=AssertionError("the room microphone must not be looked up")),
    )
    return begin


def start_arguments(**overrides):
    return SimpleNamespace(
        **{"microphone": None, "language": "pt", "seat": Seat.REMOTE, **overrides}
    )


def test_the_remote_seat_transcribes_the_meeting_and_the_mac_microphone(
    tmp_path, begin, capsys
):
    listen_cli.start(start_arguments(), tmp_path)
    sources = {
        "meeting": "AvatarRemoteMeeting.monitor",
        "human": "AvatarRemoteMicrophone.monitor",
    }
    begin.assert_called_once_with(
        tmp_path,
        listener_session.ListenerPurpose.MEETING,
        sources,
        language="pt",
        identify_speakers=True,
        seat=Seat.REMOTE,
    )
    assert json.loads(capsys.readouterr().out) == {
        "listening": True,
        "sources": sources,
    }


def test_the_meeting_source_is_named_beside_the_remote_microphone():
    assert conversation_seat.REMOTE_MEETING_SOURCE == "AvatarRemoteMeeting.monitor"
    assert (
        conversation_seat.MICROPHONE_BY_SEAT[Seat.REMOTE]
        == "AvatarRemoteMicrophone.monitor"
    )


def test_the_remote_seat_skips_the_avatar_output_guard_for_its_own_sources(
    tmp_path, begin
):
    assert listen_cli.AVATAR_OUTPUTS.match("AvatarRemoteMeeting.monitor")
    listen_cli.start(start_arguments(), tmp_path)
    begin.assert_called_once()


def test_the_room_seat_keeps_the_default_microphone_and_the_guard(
    tmp_path, begin, monkeypatch
):
    monkeypatch.setattr(listen_cli, "default_microphone", lambda: "headset")
    monkeypatch.setattr(listen_cli, "existing_sources", lambda: {"headset"})
    listen_cli.start(start_arguments(seat=Seat.ROOM), tmp_path)
    assert begin.call_args.args[2] == {
        "meeting": "@DEFAULT_MONITOR@",
        "human": "headset",
    }
    assert "seat" not in begin.call_args.kwargs
    monkeypatch.setattr(listen_cli, "default_microphone", lambda: "AvatarMicrophone")
    with pytest.raises(ValueError, match="avatar's own output"):
        listen_cli.start(start_arguments(seat=Seat.ROOM), tmp_path)


def test_a_microphone_cannot_be_named_for_the_remote_seat(tmp_path, begin):
    with pytest.raises(ValueError, match="--microphone"):
        listen_cli.start(start_arguments(microphone="headset"), tmp_path)
    begin.assert_not_called()


def test_a_conversation_still_refuses_a_remote_meeting(tmp_path, begin, monkeypatch):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.OPEN
    )
    with pytest.raises(ValueError, match="avatar-talk close"):
        listen_cli.start(start_arguments(), tmp_path)
    begin.assert_not_called()


@pytest.mark.parametrize(
    ("flags", "expected"),
    [
        ([], Seat.ROOM),
        (["--seat", "room"], Seat.ROOM),
        (["--seat", "remote"], Seat.REMOTE),
    ],
)
def test_the_seat_flag_defaults_to_the_room(monkeypatch, flags, expected):
    monkeypatch.setattr(sys, "argv", ["avatar-listen", "start", *flags])
    assert listen_cli.parse_arguments().seat is expected


def test_an_unknown_seat_is_refused(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["avatar-listen", "start", "--seat", "lounge"])
    with pytest.raises(SystemExit):
        listen_cli.parse_arguments()


def test_a_pinned_language_reaches_the_listener(tmp_path, begin, monkeypatch):
    monkeypatch.setattr(listen_cli, "selected_sources", lambda _: {"meeting": "any"})
    listen_cli.start(start_arguments(seat=Seat.ROOM), tmp_path)
    begin.assert_called_once_with(
        tmp_path,
        listener_session.ListenerPurpose.MEETING,
        {"meeting": "any"},
        language="pt",
        identify_speakers=True,
    )
