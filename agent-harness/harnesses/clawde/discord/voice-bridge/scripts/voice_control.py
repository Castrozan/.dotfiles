import json
import os
import socket
import subprocess
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
CONTROL_TIMEOUT_SECONDS = 180


def connected_control_socket(
    socket_path=CONTROL_SOCKET, timeout_seconds=CONTROL_TIMEOUT_SECONDS
):
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.settimeout(timeout_seconds)
    try:
        connection.connect(socket_path)
    except OSError:
        connection.close()
        raise
    return connection


def send_request(connection, **request):
    connection.sendall(json.dumps(request).encode() + b"\n")


def request_once(
    socket_path=CONTROL_SOCKET, timeout_seconds=CONTROL_TIMEOUT_SECONDS, **request
):
    with connected_control_socket(socket_path, timeout_seconds) as connection:
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
    subprocess.run(
        ["systemctl", "--user", action, BRIDGE_SERVICE], check=True, timeout=40
    )


def wait_for_identity(result, deadline):
    if result.get("error") != "no_eligible_available_bot_for_listener":
        return False
    if time.monotonic() >= deadline:
        return False
    state = request_once(command="status")
    return not any(identity["ready"] for identity in state["identities"])


def request_join(preferred=None, follow_listener=False):
    deadline = time.monotonic() + JOIN_DEADLINE_SECONDS
    while True:
        try:
            result = request_once(
                command="join", preferred=preferred, follow_listener=follow_listener
            )
            if not wait_for_identity(result, deadline):
                return result
        except (FileNotFoundError, ConnectionRefusedError):
            if time.monotonic() >= deadline:
                return {"error": "bridge_did_not_start"}
        time.sleep(JOIN_RETRY_SECONDS)


def request_conductor_selection(target):
    request = (
        {"command": "agent", "target": target, "default": False}
        if target
        else {"command": "status"}
    )
    deadline = time.monotonic() + JOIN_DEADLINE_SECONDS
    while True:
        try:
            return request_once(socket_path=CONDUCTOR_SOCKET, **request)
        except (FileNotFoundError, ConnectionRefusedError):
            if time.monotonic() >= deadline:
                return {"error": "conductor_did_not_start"}
            time.sleep(JOIN_RETRY_SECONDS)
