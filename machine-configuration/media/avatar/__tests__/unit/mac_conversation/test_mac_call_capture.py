import io
import sys
from contextlib import contextmanager
from unittest.mock import Mock

import listener
import mac_call_capture
import mac_seat_client
import pytest
import source_capture
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from websockets.exceptions import ConnectionClosedError, InvalidHandshake

SPECIAL_DEVICES = (
    mac_seat_client.CALL_DEVICE,
    mac_seat_client.MEETING_MICROPHONE,
)
ORDINARY_DEVICES = st.text(min_size=1).filter(
    lambda device: device not in SPECIAL_DEVICES
)


@pytest.fixture
def on_darwin(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    return listener.boundaries_of_this_machine()[0]


@contextmanager
def call_carrying(frames):
    yield frames


def connecting_to_a_call_that_carries(monkeypatch, frames):
    connect = Mock(return_value=call_carrying(frames))
    monkeypatch.setattr(mac_call_capture, "connect", connect)
    return connect


def test_the_meeting_device_captures_the_call_audio_on_a_mac(on_darwin):
    assert on_darwin(mac_seat_client.CALL_DEVICE) == [
        sys.executable,
        str(mac_seat_client.CALL_CAPTURE_PROGRAM),
    ]


def test_the_meeting_microphone_captures_through_the_seat_page_in_meeting_mode(
    on_darwin,
):
    assert on_darwin(mac_seat_client.MEETING_MICROPHONE) == [
        sys.executable,
        str(mac_seat_client.SEAT_PROGRAM),
        mac_seat_client.MEETING_FLAG,
    ]


@given(ORDINARY_DEVICES)
def test_any_other_device_captures_the_microphone_through_the_plain_seat_page(
    device,
):
    assert mac_seat_client.capture_command(device) == [
        sys.executable,
        str(mac_seat_client.SEAT_PROGRAM),
    ]


def test_the_meeting_device_keeps_the_pulse_capture_on_linux():
    capture_command = listener.boundaries_of_this_machine()[0]
    assert capture_command("meeting") == source_capture.capture_command("meeting")


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.lists(st.one_of(st.binary(), st.text()), max_size=12))
def test_every_binary_frame_of_the_call_reaches_the_capture_output_in_order(
    monkeypatch, frames
):
    connecting_to_a_call_that_carries(monkeypatch, frames)
    output = io.BytesIO()
    mac_call_capture.copy_call_audio(output)
    assert output.getvalue() == b"".join(
        frame for frame in frames if isinstance(frame, bytes)
    )


def test_the_capture_connects_to_the_call_path_of_the_seat_page_server(monkeypatch):
    connect = connecting_to_a_call_that_carries(monkeypatch, [])
    mac_call_capture.copy_call_audio(io.BytesIO())
    assert connect.call_args.args == ("ws://127.0.0.1:8772/call",)
    assert connect.call_args.kwargs["origin"] == "http://127.0.0.1:8772"
    assert connect.call_args.kwargs["open_timeout"]


@pytest.mark.parametrize(
    "failure",
    [ConnectionRefusedError(), InvalidHandshake(), ConnectionClosedError(None, None)],
)
def test_a_seat_that_is_not_there_ends_the_capture_quietly_for_the_listener_to_retry(
    monkeypatch, capsys, failure
):
    monkeypatch.setattr(mac_call_capture, "connect", Mock(side_effect=failure))
    with pytest.raises(SystemExit) as finished:
        mac_call_capture.main()
    assert finished.value.code == 1
    assert capsys.readouterr().err == ""
