import argparse
import json
import os
import socket
import subprocess
import sys
import time

BRIDGE_SERVICE = "silver-voice-bridge.service"
CONTROL_SOCKET = os.environ.get(
    "VOICE_BRIDGE_CONTROL_SOCKET",
    os.path.join(
        os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"),
        "silver-voice",
        "control.sock",
    ),
)
CONDUCTOR_SOCKET = os.environ.get(
    "VOICE_CONDUCTOR_CONTROL_SOCKET",
    os.path.join(os.path.dirname(CONTROL_SOCKET), "conductor.sock"),
)
JOIN_DEADLINE_SECONDS = 45
JOIN_RETRY_SECONDS = 0.2


def connected_control_socket(socket_path=CONTROL_SOCKET):
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.settimeout(180)
    try:
        connection.connect(socket_path)
    except OSError:
        connection.close()
        raise
    return connection


def send_request(connection, **request):
    connection.sendall(json.dumps(request).encode() + b"\n")


def request_once(socket_path=CONTROL_SOCKET, **request):
    with connected_control_socket(socket_path) as connection:
        send_request(connection, **request)
        with connection.makefile(encoding="utf-8") as replies:
            reply = replies.readline()
    if not reply:
        return {"error": "bridge_closed_the_connection"}
    return json.loads(reply)


def request_running_bridge(**request):
    try:
        return request_once(**request)
    except (FileNotFoundError, ConnectionRefusedError):
        return {"error": "bridge_not_running"}


def control_bridge_service(action):
    subprocess.run(["systemctl", "--user", action, BRIDGE_SERVICE], check=True)


def request_join():
    deadline = time.monotonic() + JOIN_DEADLINE_SECONDS
    while True:
        try:
            return request_once(command="join")
        except (FileNotFoundError, ConnectionRefusedError):
            if time.monotonic() >= deadline:
                return {"error": "bridge_did_not_start"}
            time.sleep(JOIN_RETRY_SECONDS)


def join(_arguments):
    control_bridge_service("start")
    return request_join()


def leave(_arguments):
    return request_running_bridge(command="leave")


def status(_arguments):
    return request_running_bridge(command="status")


def speak(arguments):
    return request_running_bridge(
        command="speak", text=arguments.text, language=arguments.language
    )


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
    commands.add_parser(
        "join", help="Join the voice channel the listener is in."
    ).set_defaults(handler=join)
    commands.add_parser(
        "leave", help="Leave the call; the bridge keeps watching for the next one."
    ).set_defaults(handler=leave)
    commands.add_parser("status", help="Report the call as JSON.").set_defaults(
        handler=status
    )
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
    except (OSError, ValueError) as error:
        reply = {"error": f"control_request_failed_{type(error).__name__}"}
    if reply is None:
        return 0
    print(json.dumps(reply, ensure_ascii=False))
    return 1 if "error" in reply else 0


if __name__ == "__main__":
    sys.exit(main())
