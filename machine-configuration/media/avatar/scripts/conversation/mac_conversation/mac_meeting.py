import contextlib
import json
import subprocess

import conversation_state
import listener_session
import local_seat
import local_window
import mac_seat_client
import mac_stage
import meeting_camera
from conversation_state import ConversationAction, ConversationCommand
from listener_session import ListenerPurpose

MEETING_SOURCES = {
    "meeting": mac_seat_client.CALL_DEVICE,
    "human": mac_seat_client.MEETING_MICROPHONE,
}
CONTROLS_PAGE = "controls.html"
CLEANUP_FAILURES = (OSError, RuntimeError, TimeoutError, subprocess.SubprocessError)
CALL_DEVICES_READY = (
    "Avatar ready. In the call, select the camera OBS Virtual Camera, "
    "the microphone BlackHole 2ch and the speaker BlackHole 16ch"
)
CONVERSATION_OPEN = (
    "A conversation is open on this Mac; run avatar-talk close "
    "before using the meeting commands"
)
MEETING_OPEN = (
    "A meeting is running on this Mac; run avatar-stop to end it before talking"
)
CONTROLS_NEED_A_MEETING = (
    "Run avatar-start on this Mac before opening its controls: they choose the "
    "camera of the call picture, which is not running here"
)


def refuse_talking(arguments, directory):
    raise RuntimeError(MEETING_OPEN)


REFUSALS_IN_A_MEETING = {
    ConversationAction.REFUSE_MEETING: refuse_talking,
    ConversationAction.LEAVE_MEETING: refuse_talking,
}


def refuse_while_a_conversation_is_open(directory):
    decision = conversation_state.decide(
        conversation_state.observe(directory), ConversationCommand.TRANSCRIBE_MEETING
    )
    if decision is ConversationAction.REFUSE_CONVERSATION:
        raise RuntimeError(CONVERSATION_OPEN)


def begin_listening(directory, language):
    listener_session.begin_listening(
        directory,
        ListenerPurpose.MEETING,
        MEETING_SOURCES,
        language=language,
        identify_speakers=True,
    )


def listen_to_the_call(directory, language):
    refuse_while_a_conversation_is_open(directory)
    begin_listening(directory, language)
    print(json.dumps({"listening": True, "sources": MEETING_SOURCES}))


def seat_attached_or_failed():
    seat = local_seat.health(mac_seat_client.PORT) or {}
    if seat.get("failure"):
        raise RuntimeError(f"The meeting page failed: {seat['failure']}")
    return bool(seat.get("attached"))


def end(directory):
    steps = (
        listener_session.stop_listening,
        lambda: listener_session.erase_session_records(directory),
        meeting_camera.stop,
        mac_seat_client.close_browser,
        mac_stage.strike,
    )
    failures = []
    for step in steps:
        try:
            step()
        except CLEANUP_FAILURES as failure:
            failures.append(failure)
    if failures:
        raise failures[0]


def start(directory):
    refuse_while_a_conversation_is_open(directory)
    try:
        mac_stage.set_up()
        mac_stage.show_window()
        begin_listening(directory, None)
        local_seat.wait_until(
            seat_attached_or_failed,
            mac_seat_client.STREAM_ATTACH_WAIT_SECONDS,
            mac_seat_client.NO_PAGE_MESSAGE,
        )
        meeting_camera.start()
    except BaseException:
        with contextlib.suppress(*CLEANUP_FAILURES):
            end(directory)
        raise
    print(CALL_DEVICES_READY)


def stop(directory):
    refuse_while_a_conversation_is_open(directory)
    end(directory)


def controls(directory):
    if not (mac_seat_client.attached() and meeting_camera.running()):
        raise RuntimeError(CONTROLS_NEED_A_MEETING)
    local_window.open_window(CONTROLS_PAGE, local_seat.RENDERER_PORT)
