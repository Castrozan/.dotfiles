import json
from types import SimpleNamespace
from unittest.mock import Mock

import local_seat
import mac_meeting
import mac_seat_client
import pytest
from conversation_state import ConversationPhase
from listener_session import ListenerPurpose

CLEANUP = ["stop_listening", "erase", "camera_stop", "close_browser", "strike"]
SETUP = ["set_up", "show_window", "begin"]
CONVERSATION_PHASES = [
    ConversationPhase.OPEN,
    ConversationPhase.LIVE,
    ConversationPhase.INTERRUPTED,
]


@pytest.fixture
def mac(monkeypatch, tmp_path):
    mac = SimpleNamespace(
        steps=Mock(),
        phase=ConversationPhase.CLOSED,
        seat={"attached": True},
        directory=tmp_path / "runtime",
    )
    patched = {
        mac_meeting.mac_stage: ["set_up", "show_window", "strike"],
        mac_meeting.meeting_camera: ["running"],
        mac_meeting.mac_seat_client: ["close_browser", "attached"],
        mac_meeting.local_window: ["open_window"],
    }
    for module, names in patched.items():
        for name in names:
            monkeypatch.setattr(module, name, getattr(mac.steps, name))
    monkeypatch.setattr(mac_meeting.meeting_camera, "start", mac.steps.camera_start)
    monkeypatch.setattr(mac_meeting.meeting_camera, "stop", mac.steps.camera_stop)
    session = mac_meeting.listener_session
    monkeypatch.setattr(session, "begin_listening", mac.steps.begin)
    monkeypatch.setattr(session, "stop_listening", mac.steps.stop_listening)
    monkeypatch.setattr(session, "erase_session_records", mac.steps.erase)
    monkeypatch.setattr(mac_meeting.conversation_state, "observe", lambda _: mac.phase)
    monkeypatch.setattr(local_seat, "health", lambda port: mac.seat)
    return mac


def steps_taken(mac):
    return [call[0] for call in mac.steps.mock_calls]


def test_starting_stands_the_stage_then_listens_then_opens_the_camera_and_names_the_devices(
    mac, capsys
):
    mac_meeting.start(mac.directory)
    assert steps_taken(mac) == [*SETUP, "camera_start"]
    ready = capsys.readouterr().out
    assert ready.count("\n") == 1
    for device in ("OBS Virtual Camera", "BlackHole 2ch", "BlackHole 16ch"):
        assert device in ready


def test_the_meeting_listens_to_the_call_and_the_microphone_and_knows_the_voices(mac):
    mac_meeting.start(mac.directory)
    mac.steps.begin.assert_called_once_with(
        mac.directory,
        ListenerPurpose.MEETING,
        {
            "meeting": mac_seat_client.CALL_DEVICE,
            "human": mac_seat_client.MEETING_MICROPHONE,
        },
        language=None,
        identify_speakers=True,
    )


@pytest.mark.parametrize("phase", [ConversationPhase.CLOSED, ConversationPhase.MEETING])
def test_a_meeting_starts_whether_nothing_or_an_earlier_meeting_is_running(mac, phase):
    mac.phase = phase
    mac_meeting.start(mac.directory)
    assert steps_taken(mac)[-1] == "camera_start"


@pytest.mark.parametrize("phase", CONVERSATION_PHASES)
def test_a_meeting_does_not_start_while_a_conversation_is_open_and_touches_nothing(
    mac, phase
):
    mac.phase = phase
    with pytest.raises(RuntimeError, match="avatar-talk close"):
        mac_meeting.start(mac.directory)
    assert steps_taken(mac) == []


@pytest.mark.parametrize(
    "failing_step", ["set_up", "show_window", "begin", "camera_start"]
)
def test_a_failed_start_undoes_everything_in_the_stop_order_and_reports_the_failure(
    mac, failing_step
):
    getattr(mac.steps, failing_step).side_effect = RuntimeError("it failed")
    with pytest.raises(RuntimeError, match="it failed"):
        mac_meeting.start(mac.directory)
    assert steps_taken(mac)[-len(CLEANUP) :] == CLEANUP


def test_a_page_that_reports_a_failure_ends_the_start_with_its_reason(mac):
    mac.seat = {"attached": False, "failure": "Error: missing BlackHole 16ch"}
    with pytest.raises(RuntimeError, match="missing BlackHole 16ch"):
        mac_meeting.start(mac.directory)
    assert steps_taken(mac)[-len(CLEANUP) :] == CLEANUP
    assert "camera_start" not in steps_taken(mac)


def test_a_page_that_never_attaches_ends_the_start_and_undoes_everything(
    mac, monkeypatch
):
    mac.seat = None
    monkeypatch.setattr(mac_seat_client, "STREAM_ATTACH_WAIT_SECONDS", 0)
    monkeypatch.setattr(local_seat, "POLL_SECONDS", 0)
    with pytest.raises(TimeoutError, match="did not attach"):
        mac_meeting.start(mac.directory)
    assert steps_taken(mac) == [*SETUP, *CLEANUP]


def test_an_undo_that_fails_does_not_hide_the_first_failure(mac):
    mac.steps.camera_start.side_effect = RuntimeError("OBS Studio is not installed")
    mac.steps.stop_listening.side_effect = TimeoutError("the listener did not stop")
    with pytest.raises(RuntimeError, match="OBS Studio is not installed"):
        mac_meeting.start(mac.directory)
    assert steps_taken(mac)[-len(CLEANUP) :] == CLEANUP


def test_stopping_stops_the_listener_erases_the_transcript_then_ends_the_picture_page_and_stage(
    mac,
):
    mac_meeting.stop(mac.directory)
    assert steps_taken(mac) == CLEANUP
    mac.steps.erase.assert_called_once_with(mac.directory)


def test_a_step_that_fails_while_stopping_does_not_keep_the_later_steps_from_running(
    mac,
):
    mac.steps.stop_listening.side_effect = TimeoutError("the listener did not stop")
    with pytest.raises(TimeoutError, match="the listener did not stop"):
        mac_meeting.stop(mac.directory)
    assert steps_taken(mac) == CLEANUP


@pytest.mark.parametrize("phase", CONVERSATION_PHASES)
def test_stopping_the_meeting_leaves_an_open_conversation_alone(mac, phase):
    mac.phase = phase
    with pytest.raises(RuntimeError, match="avatar-talk close"):
        mac_meeting.stop(mac.directory)
    assert steps_taken(mac) == []


def test_listening_begins_a_meeting_listener_in_the_language_and_says_what_it_hears(
    mac, capsys
):
    mac_meeting.listen_to_the_call(mac.directory, "pt")
    assert steps_taken(mac) == ["begin"]
    assert mac.steps.begin.call_args.kwargs["language"] == "pt"
    assert json.loads(capsys.readouterr().out) == {
        "listening": True,
        "sources": mac_meeting.MEETING_SOURCES,
    }


@pytest.mark.parametrize("phase", CONVERSATION_PHASES)
def test_listening_to_a_call_is_refused_while_a_conversation_is_open(mac, phase):
    mac.phase = phase
    with pytest.raises(RuntimeError, match="avatar-talk close"):
        mac_meeting.listen_to_the_call(mac.directory, None)
    assert steps_taken(mac) == []


def test_the_controls_open_beside_the_local_renderer_while_the_meeting_runs(mac):
    mac.steps.attached.return_value = True
    mac.steps.running.return_value = True
    mac_meeting.controls(mac.directory)
    mac.steps.open_window.assert_called_once_with(
        "controls.html", local_seat.RENDERER_PORT
    )


@pytest.mark.parametrize(("attached", "running"), [(False, True), (True, False)])
def test_the_controls_need_both_the_seat_page_and_the_camera(mac, attached, running):
    mac.steps.attached.return_value = attached
    mac.steps.running.return_value = running
    with pytest.raises(RuntimeError, match="Run avatar-start on this Mac"):
        mac_meeting.controls(mac.directory)
    mac.steps.open_window.assert_not_called()
