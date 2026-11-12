import enum
import json
import os
import subprocess
import sys

import conversation_addressee
import conversation_seat
import conversation_state
import desktop_window
import listen_cli
import listener_session
import start
import user_units
import utterances
from conversation_seat import Seat
from conversation_state import ConversationPhase
from listener_session import ListenerPurpose

ROOM_MICROPHONE = conversation_seat.MICROPHONE_BY_SEAT[Seat.ROOM]
PANE_ENVIRONMENT_VARIABLE = "HERDR_PANE_ID"
LIVE_NEEDS_A_PANE = (
    "avatar-talk open --live must run from an agent's herdr pane: the live voice hands "
    "the room's tasks to that agent"
)
LIVE_NEEDS_A_SERVANT = (
    "The live voice could not give the floor to this pane: only a session with a Servant "
    "name can hold it and receive the room's tasks"
)
LIVE_OWNS_THE_TURNS = (
    "The live voice speaks and listens in this conversation and sends you each task "
    "over a2a: end your turn to receive them, or run avatar-talk close"
)
COMMAND_TIMEOUT_SECONDS = 120


class WindowPresence(enum.StrEnum):
    HIDDEN = "hidden"
    SHOWN = "shown"


def room_microphone_ready():
    return ROOM_MICROPHONE in listen_cli.existing_sources()


def seat_microphone_ready(seat):
    return conversation_seat.MICROPHONE_BY_SEAT[seat] in listen_cli.existing_sources()


def status(arguments, directory):
    phase = conversation_state.observe(directory)
    is_open = phase in (ConversationPhase.OPEN, ConversationPhase.LIVE)
    print(
        json.dumps(
            {
                "open": is_open,
                "live": phase is ConversationPhase.LIVE,
                "seat": conversation_seat.configured(directory) if is_open else None,
                "last_heard": utterances.last_heard(directory),
            }
        )
    )


def show_chosen_character(arguments):
    if arguments.character:
        subprocess.run(
            ["avatar-command", "character", arguments.character],
            check=True,
            stdout=sys.stderr,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )


def open_conversation(arguments, directory):
    seat = Seat(arguments.seat)
    try:
        start.bring_up(
            conversation_state.CONVERSATION_TARGET,
            (start.renderer_ready, lambda: seat_microphone_ready(seat)),
        )
        conversation_seat.prepare(seat)
        show_chosen_character(arguments)
        listener_session.begin_listening(
            directory,
            ListenerPurpose.CONVERSATION,
            {"human": conversation_seat.MICROPHONE_BY_SEAT[seat]},
            language=arguments.language,
            barge_in=True,
            seat=seat,
        )
    except BaseException:
        close_conversation(arguments, directory)
        raise
    status(arguments, directory)


def open_live_conversation(arguments, directory):
    if not os.environ.get(PANE_ENVIRONMENT_VARIABLE):
        raise RuntimeError(LIVE_NEEDS_A_PANE)
    try:
        start.bring_up(
            conversation_state.CONVERSATION_TARGET,
            (start.renderer_ready, room_microphone_ready),
        )
        show_chosen_character(arguments)
        listener_session.begin_listening(
            directory, ListenerPurpose.LIVE, {"human": ROOM_MICROPHONE}
        )
        subprocess.run(
            ["avatar-claim-floor"], check=True, timeout=COMMAND_TIMEOUT_SECONDS
        )
        holder = conversation_addressee.current(directory)
        if holder is None or holder.pane != os.environ[PANE_ENVIRONMENT_VARIABLE]:
            raise RuntimeError(LIVE_NEEDS_A_SERVANT)
    except BaseException:
        close_conversation(arguments, directory)
        raise
    status(arguments, directory)


def refuse_live(arguments, directory):
    raise RuntimeError(LIVE_OWNS_THE_TURNS)


def keep_conversation_open(arguments, directory):
    show_chosen_character(arguments)
    status(arguments, directory)


def refuse_meeting(arguments, directory):
    raise RuntimeError("A meeting is being transcribed; stop it before talking")


def refuse_closed(arguments, directory):
    raise utterances.ConversationClosed(utterances.CLOSED_MESSAGE)


def close_conversation(arguments, directory):
    subprocess.run(
        ["avatar-command", "stop-speaking"],
        capture_output=True,
        check=False,
        timeout=COMMAND_TIMEOUT_SECONDS,
    )
    subprocess.run(
        ["systemctl", "--user", "stop", conversation_state.CONVERSATION_TARGET],
        check=True,
        timeout=listener_session.SYSTEMCTL_TIMEOUT_SECONDS,
    )
    if user_units.unit_active(start.MEETING_TARGET):
        hide_everywhere()
    else:
        subprocess.run(
            ["avatar-stop"],
            check=True,
            stdout=subprocess.DEVNULL,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    print(json.dumps({"open": False}))


def leave_meeting(arguments, directory):
    print(json.dumps({"open": False}))


def set_canvas_presence(presence):
    subprocess.run(
        ["avatar-command", "presence", presence],
        capture_output=True,
        check=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
    )


def hide_everywhere():
    set_canvas_presence(WindowPresence.HIDDEN)
    desktop_window.hide()


def show_window(arguments, directory):
    if conversation_seat.current(directory) is Seat.ROOM:
        desktop_window.show()
    set_canvas_presence(WindowPresence.SHOWN)


def hide_window(arguments, directory):
    hide_everywhere()
