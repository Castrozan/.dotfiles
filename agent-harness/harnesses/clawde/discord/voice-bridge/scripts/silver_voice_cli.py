import argparse
import json
import subprocess
import sys

from voice_control import (
    CONDUCTOR_SOCKET,
    connected_control_socket,
    request_once,
    request_running_bridge,
    send_request,
)
from voice_setup import join, meeting_start


def leave(_arguments):
    return request_running_bridge(command="leave")


def status(_arguments):
    return request_running_bridge(command="status")


def speak(arguments):
    return request_running_bridge(
        command="speak", text=arguments.text, language=arguments.language
    )


def presentation(arguments):
    request = {"command": arguments.command}
    if arguments.command != "catalog":
        request["name"] = arguments.name
    return request_running_bridge(**request)


def agent(arguments):
    request = {"command": "status"}
    if arguments.target or arguments.default:
        request = {
            "command": "agent",
            "target": arguments.target,
            "default": arguments.default,
        }
    try:
        return request_once(socket_path=CONDUCTOR_SOCKET, **request)
    except (FileNotFoundError, ConnectionRefusedError):
        return {"error": "conductor_not_running"}


def follow(arguments):
    try:
        connection = connected_control_socket()
    except (FileNotFoundError, ConnectionRefusedError):
        return {"error": "bridge_not_running"}
    with connection:
        connection.settimeout(None)
        send_request(connection, command="follow", after=arguments.after)
        with connection.makefile(encoding="utf-8") as lines:
            for line in lines:
                print(line, end="", flush=True)
    return None


def parse_arguments(arguments=None):
    parser = argparse.ArgumentParser(
        prog="discord-voice",
        description="Carry an authorized listener's speech and agent replies through Discord voice.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    join_parser = commands.add_parser(
        "join",
        aliases=["join-me"],
        help="Join using an available authorized bot and the configured or explicit answering agent.",
    )
    join_parser.set_defaults(handler=join)
    join_parser.add_argument(
        "--bot", help="Preferred configured bot; never replaces an owned active call."
    )
    join_parser.add_argument(
        "--agent",
        help="Answering live A2A peer; otherwise the current configured responder is reported.",
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
        "catalog", help="List shared avatar characters and speech models."
    ).set_defaults(handler=presentation)
    commands.add_parser(
        "meeting-start",
        help="Prepare fresh existing Avatar Cam/AvatarMicrophone without physical capture; first leave Discord to prevent feedback. Existing avatar lifecycle owns these devices, not this bridge.",
    ).set_defaults(handler=meeting_start)
    for command in ("character", "model"):
        selection_parser = commands.add_parser(
            command, help=f"Select the speech {command}; resets on restart."
        )
        selection_parser.add_argument("name")
        selection_parser.set_defaults(handler=presentation)
    speak_parser = commands.add_parser(
        "speak", help="Say text in the call; returns when finished or interrupted."
    )
    speak_parser.set_defaults(handler=speak)
    speak_parser.add_argument("text")
    speak_parser.add_argument("--language", choices=("pt-br", "en-us"), default="pt-br")
    follow_parser = commands.add_parser(
        "follow", help="Stream the listener's transcribed lines as JSON."
    )
    follow_parser.set_defaults(handler=follow)
    follow_parser.add_argument(
        "--after", type=int, help="Replay retained lines after this sequence."
    )
    agent_parser = commands.add_parser(
        "agent",
        help="Show or select the answering A2A conversation; selection resets on restart.",
        description="Select a live A2A conversation with native completed-reply capture through Herdr Pace.",
    )
    agent_parser.set_defaults(handler=agent)
    selection = agent_parser.add_mutually_exclusive_group()
    selection.add_argument(
        "target", nargs="?", help="Live A2A peer, pane, Servant or session ID."
    )
    selection.add_argument(
        "--default",
        action="store_true",
        help="Restore the declarative answering agent.",
    )
    return parser.parse_args(arguments)


def main():
    arguments = parse_arguments()
    try:
        reply = arguments.handler(arguments)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        reply = {"error": f"control_request_failed_{type(error).__name__}"}
    if reply is None:
        return 0
    print(json.dumps(reply, ensure_ascii=False))
    return 1 if "error" in reply else 0


if __name__ == "__main__":
    sys.exit(main())
