from __future__ import annotations

import json
import os
import socket
import subprocess

HERDR_COMMAND_TIMEOUT_SECONDS = 5
WORKSPACE_EVENT_TYPES = ("pane.agent_detected", "pane.exited", "pane.closed")


class HerdrUnavailable(Exception):
    pass


def workspace_agent_panes(workspace: str) -> list[dict]:
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
    return [pane for pane in panes if pane.get("agent")]


def subscribed_socket(subscriptions: list[dict]) -> socket.socket:
    socket_path = os.environ.get("HERDR_SOCKET_PATH")
    if not socket_path:
        raise HerdrUnavailable("HERDR_SOCKET_PATH is unset; run inside herdr")
    connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    connection.connect(socket_path)
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
