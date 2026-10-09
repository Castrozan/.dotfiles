from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from urllib.parse import quote

DEFAULT_DAEMON_ENDPOINT = "http://127.0.0.1:7000"
TERMINAL_TASK_STATES = frozenset({"completed", "canceled", "failed"})
DIRECTORY_REQUEST_TIMEOUT_SECONDS = 5.0
TASK_REQUEST_TIMEOUT_SECONDS = 10.0
DEFAULT_ANSWER_TIMEOUT_SECONDS = 900.0
POLL_INTERVAL_SECONDS = 2.0


class PeerRequestFailure(Exception):
    pass


def request_peer_json(
    method: str,
    url: str,
    payload: dict | None = None,
    timeout_seconds: float = TASK_REQUEST_TIMEOUT_SECONDS,
) -> tuple[int, dict]:
    body_bytes = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url=url, data=body_bytes, method=method)
    if body_bytes is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as http_error:
        try:
            return http_error.code, json.loads(http_error.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return http_error.code, {}
    except (urllib.error.URLError, TimeoutError, ConnectionError) as transport_failure:
        raise PeerRequestFailure(
            f"{url} is unreachable: {transport_failure}"
        ) from transport_failure


def read_agent_directory(daemon_endpoint: str) -> dict:
    status_code, document = request_peer_json(
        "GET",
        f"{daemon_endpoint.rstrip('/')}/agents",
        timeout_seconds=DIRECTORY_REQUEST_TIMEOUT_SECONDS,
    )
    if status_code != 200:
        raise PeerRequestFailure(
            f"the a2a daemon at {daemon_endpoint} answered {status_code} "
            "instead of listing its agents"
        )
    return {entry["name"]: entry for entry in document.get("agents", [])}


def resolve_peer_endpoint(agent_directory: dict, agent_target: str) -> str:
    agent = next(
        (
            entry
            for entry in agent_directory.values()
            if entry.get("paneId") == agent_target
        ),
        agent_directory.get(agent_target),
    )
    if agent is None:
        attached_agent_names = ", ".join(sorted(agent_directory)) or "none attached"
        raise PeerRequestFailure(
            f"unknown agent {agent_target!r}; attached agents: {attached_agent_names}"
        )
    return agent["endpoint"].rstrip("/")


def notify_peer(endpoint: str, claimed_sender: str, content: str) -> dict:
    status_code, receipt = request_peer_json(
        "POST",
        f"{endpoint}/messages",
        {"claimedSender": claimed_sender, "content": content},
    )
    if status_code != 202:
        raise PeerRequestFailure(
            f"peer refused the notification with status {status_code}: {receipt}"
        )
    return receipt


def read_peer_inbox(endpoint: str) -> dict:
    status_code, inbox = request_peer_json("GET", f"{endpoint}/messages")
    if status_code != 200:
        raise PeerRequestFailure(f"peer inbox returned status {status_code}: {inbox}")
    return inbox


def acknowledge_peer_notification(endpoint: str, notification_identifier: str) -> dict:
    status_code, receipt = request_peer_json(
        "POST", f"{endpoint}/messages/{quote(notification_identifier, safe='')}/ack"
    )
    if status_code != 200:
        raise PeerRequestFailure(
            f"peer refused acknowledgement with status {status_code}: {receipt}"
        )
    return receipt


def submit_task_to_peer(endpoint: str, input_text: str) -> dict:
    status_code, task = request_peer_json(
        "POST", f"{endpoint}/tasks/send", {"input": input_text}
    )
    if status_code == 409:
        raise PeerRequestFailure(
            f"peer is already working on task {task.get('id', 'unknown')}; "
            "cancel it or wait for it to finish"
        )
    if status_code != 201:
        raise PeerRequestFailure(
            f"peer refused the task with status {status_code}: {task}"
        )
    return task


def read_task_from_peer(endpoint: str, task_id: str) -> dict:
    status_code, task = request_peer_json("GET", f"{endpoint}/tasks/{task_id}")
    if status_code != 200:
        raise PeerRequestFailure(f"task {task_id} not found on {endpoint}")
    return task


def cancel_task_on_peer(endpoint: str, task_id: str) -> dict:
    status_code, task = request_peer_json("POST", f"{endpoint}/tasks/{task_id}/cancel")
    if status_code != 200:
        raise PeerRequestFailure(f"task {task_id} not found on {endpoint}")
    return task


def poll_task_until_terminal(
    endpoint: str, task_id: str, timeout_seconds: float
) -> dict:
    deadline_monotonic_seconds = time.monotonic() + timeout_seconds
    while True:
        task = read_task_from_peer(endpoint, task_id)
        if task.get("state") in TERMINAL_TASK_STATES:
            return task
        if time.monotonic() >= deadline_monotonic_seconds:
            raise PeerRequestFailure(
                f"task {task_id} is still {task.get('state')} after "
                f"{timeout_seconds:.0f}s; read it later with a2a status"
            )
        time.sleep(POLL_INTERVAL_SECONDS)
