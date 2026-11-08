from __future__ import annotations

import json
import os
import socket
import subprocess
from pathlib import Path

HERDR_COMMAND_TIMEOUT_SECONDS = 5
WORKSPACE_EVENT_TYPES = ("pane.agent_detected", "pane.exited", "pane.closed")


class HerdrUnavailable(Exception):
    pass


def workspace_panes(workspace: str) -> list[dict]:
    try:
        completed = subprocess.run(
            ["herdr", "pane", "list", "--workspace", workspace],
            capture_output=True,
            text=True,
            check=False,
            timeout=HERDR_COMMAND_TIMEOUT_SECONDS,
        )
        panes = json.loads(completed.stdout)["result"]["panes"]
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError) as failure:
        raise HerdrUnavailable(
            f"cannot list panes of {workspace}: {failure}"
        ) from failure
    return panes


def herdr_socket_path() -> Path:
    explicit_path = os.environ.get("HERDR_SOCKET_PATH")
    if explicit_path:
        return Path(explicit_path)
    configuration_directory = Path.home() / ".config" / "herdr"
    session = os.environ.get("HERDR_SESSION")
    if session:
        return configuration_directory / "sessions" / session / "herdr.sock"
    return configuration_directory / "herdr.sock"


def subscribed_socket(subscriptions: list[dict]) -> socket.socket:
    socket_path = herdr_socket_path()
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        connection.connect(str(socket_path))
    except OSError as failure:
        connection.close()
        raise HerdrUnavailable(
            f"cannot reach herdr at {socket_path}: {failure}"
        ) from failure
    request = {
        "id": "orchestrator-watch",
        "method": "events.subscribe",
        "params": {"subscriptions": subscriptions},
    }
    connection.sendall((json.dumps(request) + "\n").encode())
    return connection


def status_subscription(pane_id: str) -> list[dict]:
    return [{"type": "pane.agent_status_changed", "pane_id": pane_id}]


def workspace_subscription() -> list[dict]:
    return [{"type": event_type} for event_type in WORKSPACE_EVENT_TYPES]


def decoded_messages(buffer: bytes) -> tuple[list[dict], bytes]:
    *complete_lines, remainder = buffer.split(b"\n")
    messages = []
    for line in complete_lines:
        try:
            messages.append(json.loads(line))
        except ValueError:
            continue
    return messages, remainder
