import enum
import json
import subprocess
import sys

import conversation_state
import desktop_window
import listen_cli
import listener_session
import start
import user_units
import utterances
from conversation_state import ConversationPhase
from listener_session import ListenerPurpose

ROOM_MICROPHONE = "AvatarRoomMicrophone"
FOLLOW_SLICE_SECONDS = 30
COMMAND_TIMEOUT_SECONDS = 120
SPEECH_TIMEOUT_SECONDS = 310
VOICE_TAG = "[voice]"


class WindowPresence(enum.StrEnum):
    HIDDEN = "hidden"
    SHOWN = "shown"


def room_microphone_ready():
    return ROOM_MICROPHONE in listen_cli.existing_sources()


def status(arguments, directory):
    print(
        json.dumps(
            {
                "open": conversation_state.observe(directory) is ConversationPhase.OPEN,
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
    try:
        start.bring_up(
            conversation_state.CONVERSATION_TARGET,
            (start.renderer_ready, room_microphone_ready),
        )
        show_chosen_character(arguments)
        listener_session.begin_listening(
            directory,
            ListenerPurpose.CONVERSATION,
            {"human": ROOM_MICROPHONE},
            language=arguments.language,
            barge_in=True,
        )
    except BaseException:
        close_conversation(arguments, directory)
        raise
    status(arguments, directory)


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
        apply_presence(WindowPresence.HIDDEN)
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


def speech_command(arguments):
    voice = [arguments.voice] if arguments.voice else []
    return [
        "avatar-command",
        "speak",
        arguments.text,
        arguments.emotion,
        "speakers",
        *voice,
    ]


def say(arguments, directory):
    sys.exit(
        subprocess.run(
            speech_command(arguments), timeout=SPEECH_TIMEOUT_SECONDS
        ).returncode
    )


def print_next_utterance(directory, wait_seconds):
    utterance = utterances.next_utterance(
        directory,
        wait_seconds,
        lambda: conversation_state.observe(directory) is ConversationPhase.OPEN,
    )
    if utterance:
        print(f"{VOICE_TAG} {utterance}", flush=True)


def hear(arguments, directory):
    with utterances.exclusive_consumer(directory):
        print_next_utterance(directory, arguments.wait)


def ask(arguments, directory):
    with utterances.exclusive_consumer(directory):
        subprocess.run(
            speech_command(arguments),
            check=True,
            stdout=subprocess.DEVNULL,
            timeout=SPEECH_TIMEOUT_SECONDS,
        )
        print_next_utterance(directory, arguments.wait)


def follow(arguments, directory):
    with utterances.exclusive_consumer(directory):
        while True:
            print_next_utterance(directory, FOLLOW_SLICE_SECONDS)


def set_canvas_presence(presence):
    subprocess.run(
        ["avatar-command", "presence", presence],
        capture_output=True,
        check=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
    )


def apply_presence(presence):
    if presence is WindowPresence.SHOWN:
        desktop_window.show()
        set_canvas_presence(presence)
    else:
        set_canvas_presence(presence)
        desktop_window.hide()


def show_window(arguments, directory):
    apply_presence(WindowPresence.SHOWN)


def hide_window(arguments, directory):
    apply_presence(WindowPresence.HIDDEN)
