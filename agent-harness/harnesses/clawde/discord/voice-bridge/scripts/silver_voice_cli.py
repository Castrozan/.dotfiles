import argparse
import json
import os
import socket
import subprocess
import sys
import time

BRIDGE_SERVICE = "silver-voice-bridge.service"
CONTROL_SOCKET = os.path.join(
    os.environ["XDG_RUNTIME_DIR"], "silver-voice", "control.sock"
)
JOIN_DEADLINE_SECONDS = 45
JOIN_RETRY_SECONDS = 0.2


def connected_control_socket():
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.connect(CONTROL_SOCKET)
    return connection


def send_request(connection, **request):
    connection.sendall(json.dumps(request).encode() + b"\n")


def request_once(**request):
    with connected_control_socket() as connection:
        send_request(connection, **request)
        reply = connection.makefile(encoding="utf-8").readline()
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
    reply = request_join()
    if "error" in reply:
        control_bridge_service("stop")
    return reply


def leave(_arguments):
    control_bridge_service("stop")
    return {"joined": False}


def status(_arguments):
    return request_running_bridge(command="status")


def speak(arguments):
    return request_running_bridge(
        command="speak", text=arguments.text, language=arguments.language
    )


def follow(arguments):
    try:
        connection = connected_control_socket()
    except (FileNotFoundError, ConnectionRefusedError):
        return {"error": "bridge_not_running"}
    with connection:
        send_request(connection, command="follow", after=arguments.after)
        for line in connection.makefile(encoding="utf-8"):
            print(line, end="", flush=True)
    return None


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="silver-voice",
        description="Carry the listener's speech and Silver's replies through a Discord voice call.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "join", help="Join the voice channel the listener is in."
    ).set_defaults(handler=join)
    commands.add_parser(
        "leave", help="Leave the call and stop the bridge."
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
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    reply = arguments.handler(arguments)
    if reply is None:
        return 0
    print(json.dumps(reply, ensure_ascii=False))
    return 1 if "error" in reply else 0


if __name__ == "__main__":
    sys.exit(main())
