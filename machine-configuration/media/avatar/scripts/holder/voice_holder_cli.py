import argparse
import signal
import subprocess
import sys

import hermes_turn
import listener_runtime
import utterances
import voice_turns
from default_holder import DefaultHolder, configured
from voice_holder import FloorHolder

OPEN_TIMEOUT_SECONDS = 180
CLOSE_TIMEOUT_SECONDS = 120
CONVERSATION_NOT_OURS = (
    "A conversation was already open without this holder; it was left alone"
)


class HolderStopped(Exception):
    pass


def parse_arguments(arguments=None):
    parser = argparse.ArgumentParser(prog="avatar-voice-holder")
    parser.add_argument("--hermes-profile", required=True)
    parser.add_argument("--character")
    return parser.parse_args(arguments)


def open_conversation(holder):
    character = ["--character", holder.character] if holder.character else []
    subprocess.run(
        [
            "avatar-talk",
            "open",
            "--seat",
            "discord",
            "--holder",
            holder.profile,
            *character,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        timeout=OPEN_TIMEOUT_SECONDS,
    )


def close_conversation():
    subprocess.run(
        ["avatar-talk", "close"],
        check=False,
        stdout=subprocess.DEVNULL,
        timeout=CLOSE_TIMEOUT_SECONDS,
    )


def stop_requested(signal_number, frame):
    raise HolderStopped


def hold_the_conversation(holder, directory):
    open_conversation(holder)
    if configured(directory) != holder:
        raise RuntimeError(CONVERSATION_NOT_OURS)
    FloorHolder(
        directory,
        holder,
        lambda heard: hermes_turn.reply_to(holder.profile, heard),
        voice_turns.speak_on_seat,
    ).hold()


def main():
    arguments = parse_arguments()
    holder = DefaultHolder(arguments.hermes_profile, arguments.character)
    signal.signal(signal.SIGTERM, stop_requested)
    try:
        hold_the_conversation(holder, listener_runtime.runtime_directory())
    except utterances.ConversationClosed:
        return 0
    except HolderStopped:
        close_conversation()
        return 0
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
