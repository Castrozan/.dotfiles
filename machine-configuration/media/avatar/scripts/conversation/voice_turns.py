import os
import subprocess
import sys

import conversation_addressee
import conversation_seat
import conversation_state
import utterances
from conversation_state import ConversationPhase

FOLLOW_SLICE_SECONDS = 30
SPEECH_TIMEOUT_SECONDS = 310
VOICE_TAG = "[voice]"
PANE_ENVIRONMENT_VARIABLE = "HERDR_PANE_ID"


def speech_command(arguments, directory):
    voice = [arguments.voice] if arguments.voice else []
    return [
        "avatar-command",
        "speak",
        arguments.text,
        arguments.emotion,
        conversation_seat.SPEECH_OUTPUT_BY_SEAT[conversation_seat.current(directory)],
        *voice,
    ]


def say(arguments, directory):
    sys.exit(
        subprocess.run(
            speech_command(arguments, directory), timeout=SPEECH_TIMEOUT_SECONDS
        ).returncode
    )


def print_next_utterance(
    directory, wait_seconds, still_addressed=utterances.always_addressed
):
    utterance = utterances.next_utterance(
        directory,
        wait_seconds,
        lambda: conversation_state.observe(directory) is ConversationPhase.OPEN,
        still_addressed,
    )
    if utterance:
        print(f"{VOICE_TAG} {utterance}", flush=True)


def hear(arguments, directory):
    with utterances.exclusive_consumer(directory):
        print_next_utterance(directory, arguments.wait)


def ask(arguments, directory):
    with utterances.exclusive_consumer(directory):
        subprocess.run(
            speech_command(arguments, directory),
            check=True,
            stdout=subprocess.DEVNULL,
            timeout=SPEECH_TIMEOUT_SECONDS,
        )
        print_next_utterance(directory, arguments.wait)


def follow(arguments, directory):
    pane = os.environ.get(PANE_ENVIRONMENT_VARIABLE)

    def still_addressed():
        return conversation_addressee.addresses(directory, pane)

    with utterances.exclusive_consumer(directory):
        while still_addressed():
            print_next_utterance(directory, FOLLOW_SLICE_SECONDS, still_addressed)
    successor = conversation_addressee.current(directory)
    name = successor.servant if successor else "another session"
    print(f"{VOICE_TAG} The room turned to {name}; this follow has ended.", flush=True)
