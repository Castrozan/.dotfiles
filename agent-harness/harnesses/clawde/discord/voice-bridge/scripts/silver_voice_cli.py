import argparse
import json
import subprocess
import sys

from voice_control import request_running_bridge
from voice_provider.provider_commands import capture, hush, play
from voice_setup import join


def leave(_arguments):
    return request_running_bridge(command="leave")


def status(_arguments):
    return request_running_bridge(command="status")


def parse_arguments(arguments=None):
    parser = argparse.ArgumentParser(
        prog="discord-voice",
        description="Discord transport for the avatar. Calls run through avatar-talk open --seat discord; this CLI joins, leaves, reports status and carries capture, play and hush.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    join_parser = commands.add_parser(
        "join",
        aliases=["join-me"],
        help="Join the listener's voice channel using an available authorized bot.",
    )
    join_parser.set_defaults(handler=join)
    join_parser.add_argument(
        "--bot", help="Preferred configured bot; never replaces an owned active call."
    )
    join_parser.add_argument(
        "--follow-listener",
        action="store_true",
        help="Explicitly follow the listener between allowed voice channels until leave.",
    )
    commands.add_parser(
        "leave", help="Leave the call and disable automatic following."
    ).set_defaults(handler=leave)
    commands.add_parser("status", help="Report the call as JSON.").set_defaults(
        handler=status
    )
    commands.add_parser(
        "capture",
        help="Stream the listener's call audio to stdout as raw s16le 16 kHz mono PCM, with silence frames while nobody speaks.",
    ).set_defaults(handler=capture)
    play_parser = commands.add_parser(
        "play",
        help="Play a 16-bit PCM WAV into the call; returns when finished or hushed. SIGTERM hushes it.",
    )
    play_parser.set_defaults(handler=play)
    play_parser.add_argument("wav")
    commands.add_parser(
        "hush", help="Stop whatever the bridge is playing into the call at once."
    ).set_defaults(handler=hush)
    return parser.parse_args(arguments)


def main():
    arguments = parse_arguments()
    try:
        reply = arguments.handler(arguments)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        reply = {"error": f"control_request_failed_{type(error).__name__}"}
    if isinstance(reply, int):
        return reply
    print(json.dumps(reply, ensure_ascii=False))
    return 1 if "error" in reply else 0


if __name__ == "__main__":
    sys.exit(main())
