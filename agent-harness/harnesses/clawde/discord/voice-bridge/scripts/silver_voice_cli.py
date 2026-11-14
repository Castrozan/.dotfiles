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


def request_join(preferred=None, follow_listener=False):
    deadline = time.monotonic() + JOIN_DEADLINE_SECONDS
    while True:
        try:
            result = request_once(
                command="join", preferred=preferred, follow_listener=follow_listener
            )
            if result.get("error") != "no_eligible_available_bot_for_listener":
                return result
            state = request_once(command="status")
            if (
                any(identity["ready"] for identity in state["identities"])
                or time.monotonic() >= deadline
            ):
                return result
            time.sleep(JOIN_RETRY_SECONDS)
        except (FileNotFoundError, ConnectionRefusedError):
            if time.monotonic() >= deadline:
                return {"error": "bridge_did_not_start"}
            time.sleep(JOIN_RETRY_SECONDS)


def join(arguments):
    meeting = subprocess.run(
        ["systemctl", "--user", "is-active", "avatar.target"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    if meeting.stdout.strip() in {"active", "activating", "reloading"}:
        return {"error": "meeting_devices_active_leave_meeting_before_discord"}
    control_bridge_service("start")
    deadline = time.monotonic() + JOIN_DEADLINE_SECONDS
    while True:
        try:
            conversation = request_once(
                socket_path=CONDUCTOR_SOCKET,
                **(
                    {"command": "agent", "target": arguments.agent, "default": False}
                    if arguments.agent
                    else {"command": "status"}
                ),
            )
            break
        except (FileNotFoundError, ConnectionRefusedError):
            if time.monotonic() >= deadline:
                return {"error": "conductor_did_not_start"}
            time.sleep(JOIN_RETRY_SECONDS)
    if "error" in conversation:
        return conversation
    result = request_join(
        arguments.bot or arguments.agent or "primary", arguments.follow_listener
    )
    return {**result, "conversation": conversation}


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


def meeting_start(_arguments):
    state = request_running_bridge(command="status")
    if "error" in state:
        return state
    if state["joined"]:
        return {"error": "leave_discord_before_meeting_microphone_use"}
    prepared = subprocess.run(
        ["avatar-start", "--virtual-only"], capture_output=True, text=True, timeout=65
    )
    if prepared.returncode:
        return {
            "error": "virtual_meeting_preparation_failed",
            "detail": prepared.stderr.strip(),
        }
    devices = json.loads(prepared.stdout)
    character = state["speech"]["character"]
    if character:
        changed = subprocess.run(
            ["avatar-command", "character", character],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if changed.returncode:
            return {
                **devices,
                "error": "meeting_character_failed",
                "detail": changed.stderr.strip(),
                "runtime": "avatar.target remains active under avatar lifecycle ownership",
            }
        confirmed = subprocess.run(
            ["avatar-command", "status"], capture_output=True, text=True, timeout=15
        )
        if (
            confirmed.returncode
            or json.loads(confirmed.stdout).get("currentCharacter") != character
        ):
            return {**devices, "error": "meeting_character_not_confirmed"}
    return {
        **devices,
        "speech": state["speech"],
        "speech_command": "avatar-command speak TEXT EMOTION mic VOICE MODEL",
        "automatic_discord_receive": False,
    }


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
