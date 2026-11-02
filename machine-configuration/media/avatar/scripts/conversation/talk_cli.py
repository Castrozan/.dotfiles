import argparse
import json
import subprocess
import sys

import listen_cli
import listener
import start
import utterances

CONVERSATION_TARGET = "avatar-conversation.target"
ROOM_MICROPHONE = "AvatarRoomMicrophone"
HEAR_WAIT_SECONDS = 100
FOLLOW_SLICE_SECONDS = 30


def is_active(unit):
    return (
        subprocess.run(["systemctl", "--user", "is-active", "--quiet", unit]).returncode
        == 0
    )


def conversation_open():
    return is_active(CONVERSATION_TARGET) and listen_cli.listening()


def room_microphone_ready():
    return ROOM_MICROPHONE in listen_cli.existing_sources()


def report(directory):
    print(
        json.dumps(
            {
                "open": conversation_open(),
                "last_heard": utterances.last_heard(directory),
            }
        )
    )


def open_conversation(arguments, directory):
    if conversation_open():
        report(directory)
        return
    if listen_cli.listening():
        raise RuntimeError("A meeting is being transcribed; stop it before talking")
    try:
        start.bring_up(
            CONVERSATION_TARGET, (start.renderer_ready, room_microphone_ready)
        )
        subprocess.run(
            ["avatar-command", "presence", "shown"], capture_output=True, check=True
        )
        listen_cli.begin_listening(
            directory,
            {"human": ROOM_MICROPHONE},
            language=arguments.language,
            barge_in=True,
        )
        utterances.forget(directory)
    except BaseException:
        close_conversation(arguments, directory)
        raise
    report(directory)


def close_conversation(arguments, directory):
    subprocess.run(
        ["avatar-command", "stop-speaking"], capture_output=True, check=False
    )
    subprocess.run(["systemctl", "--user", "stop", CONVERSATION_TARGET], check=True)
    if is_active(start.MEETING_TARGET):
        subprocess.run(
            ["avatar-command", "presence", "hidden"], capture_output=True, check=True
        )
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


def hear(arguments, directory):
    utterance = utterances.next_utterance(directory, arguments.wait, conversation_open)
    if utterance:
        print(utterance)


def ask(arguments, directory):
    if not conversation_open():
        raise utterances.ConversationClosed(utterances.CLOSED_MESSAGE)
    subprocess.run(speech_command(arguments), check=True, stdout=subprocess.DEVNULL)
    hear(arguments, directory)


def follow(arguments, directory):
    while True:
        utterance = utterances.next_utterance(
            directory, FOLLOW_SLICE_SECONDS, conversation_open
        )
        if utterance:
            print(utterance, flush=True)


def status(arguments, directory):
    report(directory)


def parse_arguments():
    parser = argparse.ArgumentParser(prog="avatar-talk")
    commands = parser.add_subparsers(dest="action", required=True)
    opening = commands.add_parser("open")
    opening.add_argument("--language")
    speaking = commands.add_parser("say")
    asking = commands.add_parser("ask")
    for parser_with_speech in (speaking, asking):
        parser_with_speech.add_argument("text")
        parser_with_speech.add_argument("emotion", nargs="?", default="neutral")
        parser_with_speech.add_argument("--voice")
    hearing = commands.add_parser("hear")
    for parser_with_wait in (asking, hearing):
        parser_with_wait.add_argument("--wait", type=float, default=HEAR_WAIT_SECONDS)
    for name in ("follow", "status", "close"):
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
