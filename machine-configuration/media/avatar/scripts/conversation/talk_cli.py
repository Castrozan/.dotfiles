import argparse
import json
import subprocess
import sys

import desktop_window
import listen_cli
import listener
import listener_session
import start
import user_units
import utterances
from listener_session import ListenerPurpose

ROOM_MICROPHONE = "AvatarRoomMicrophone"
HEAR_WAIT_SECONDS = 100
FOLLOW_SLICE_SECONDS = 30
VOICE_TAG = "[voice]"
CONVERSATION_TARGET = start.CONVERSATION_TARGET


def conversation_open(directory):
    return user_units.unit_active(
        CONVERSATION_TARGET
    ) and listener_session.listening_for(directory, ListenerPurpose.CONVERSATION)


def room_microphone_ready():
    return ROOM_MICROPHONE in listen_cli.existing_sources()


def status(arguments, directory):
    print(
        json.dumps(
            {
                "open": conversation_open(directory),
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
        )


def open_conversation(arguments, directory):
    if conversation_open(directory):
        show_chosen_character(arguments)
        status(arguments, directory)
        return
    if listener_session.listening_for(directory, ListenerPurpose.MEETING):
        raise RuntimeError("A meeting is being transcribed; stop it before talking")
    try:
        start.bring_up(
            CONVERSATION_TARGET, (start.renderer_ready, room_microphone_ready)
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


def close_conversation(arguments, directory):
    subprocess.run(
        ["avatar-command", "stop-speaking"], capture_output=True, check=False
    )
    subprocess.run(["systemctl", "--user", "stop", CONVERSATION_TARGET], check=True)
    if user_units.unit_active(start.MEETING_TARGET):
        hide_window(arguments, directory)
    else:
        subprocess.run(["avatar-stop"], check=True, stdout=subprocess.DEVNULL)
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
    sys.exit(subprocess.run(speech_command(arguments)).returncode)


def print_next_utterance(directory, wait_seconds):
    utterance = utterances.next_utterance(
        directory, wait_seconds, lambda: conversation_open(directory)
    )
    if utterance:
        print(f"{VOICE_TAG} {utterance}", flush=True)


def hear(arguments, directory):
    with utterances.exclusive_consumer(directory):
        print_next_utterance(directory, arguments.wait)


def ask(arguments, directory):
    with utterances.exclusive_consumer(directory):
        if not conversation_open(directory):
            raise utterances.ConversationClosed(utterances.CLOSED_MESSAGE)
        subprocess.run(speech_command(arguments), check=True, stdout=subprocess.DEVNULL)
        print_next_utterance(directory, arguments.wait)


def follow(arguments, directory):
    with utterances.exclusive_consumer(directory):
        while True:
            print_next_utterance(directory, FOLLOW_SLICE_SECONDS)


def set_canvas_presence(presence):
    subprocess.run(
        ["avatar-command", "presence", presence], capture_output=True, check=True
    )


def show_window(arguments, directory):
    if not conversation_open(directory):
        raise utterances.ConversationClosed(utterances.CLOSED_MESSAGE)
    desktop_window.show()
    set_canvas_presence("shown")


def hide_window(arguments, directory):
    set_canvas_presence("hidden")
    desktop_window.hide()


def parse_arguments():
    parser = argparse.ArgumentParser(prog="avatar-talk")
    commands = parser.add_subparsers(dest="action", required=True)
    opening = commands.add_parser("open")
    opening.add_argument("--language")
    opening.add_argument("--character")
    speaking = commands.add_parser("say")
    asking = commands.add_parser("ask")
    for parser_with_speech in (speaking, asking):
        parser_with_speech.add_argument("text")
        parser_with_speech.add_argument("emotion", nargs="?", default="neutral")
        parser_with_speech.add_argument("--voice")
    hearing = commands.add_parser("hear")
    for parser_with_wait in (asking, hearing):
        parser_with_wait.add_argument("--wait", type=float, default=HEAR_WAIT_SECONDS)
    for name in ("follow", "status", "show", "hide", "close"):
        commands.add_parser(name)
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    actions = {
        "open": open_conversation,
        "ask": ask,
        "say": say,
        "hear": hear,
        "follow": follow,
        "status": status,
        "show": show_window,
        "hide": hide_window,
        "close": close_conversation,
    }
    try:
        actions[arguments.action](arguments, listener.runtime_directory())
    except (
        utterances.ConversationClosed,
        subprocess.CalledProcessError,
        RuntimeError,
        TimeoutError,
        ValueError,
    ) as error:
        print(error, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
