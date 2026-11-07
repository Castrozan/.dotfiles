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


def decoded_json_object(raw_body: bytes) -> dict | None:
    try:
        document = json.loads(raw_body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return document if isinstance(document, dict) else None


def successful_json_object_answer(url: str, response) -> tuple[int, dict]:
    document = decoded_json_object(response.read())
    if document is None:
        raise PeerRequestFailure(
            f"{url} answered {response.status} without a JSON object"
        )
    return response.status, document


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
            return successful_json_object_answer(url, response)
    except urllib.error.HTTPError as http_error:
        return http_error.code, decoded_json_object(http_error.read()) or {}
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


def peer_label(agent: dict) -> str:
    servant_name = agent.get("servant")
    return f"{agent['name']} ({servant_name})" if servant_name else agent["name"]


def peers_matching_target(agent_directory: dict, agent_target: str) -> list[dict]:
    peers = list(agent_directory.values())
    target_casefolded = agent_target.casefold()
    for matches in (
        [entry for entry in peers if entry.get("paneId") == agent_target],
        [agent_directory[agent_target]] if agent_target in agent_directory else [],
        [entry for entry in peers if entry.get("sessionId") == agent_target],
        [
            entry
            for entry in peers
            if entry.get("servant") and entry["servant"].casefold() == target_casefolded
        ],
    ):
        if matches:
            return matches
    return []


def resolve_peer_endpoint(agent_directory: dict, agent_target: str) -> str:
    matches = peers_matching_target(agent_directory, agent_target)
    if len(matches) > 1:
        candidates = ", ".join(
            f"{peer_label(entry)} at {entry.get('paneId', 'unknown pane')}"
            for entry in sorted(matches, key=lambda entry: entry["name"])
        )
        raise PeerRequestFailure(
            f"{agent_target!r} names more than one live peer: {candidates}; "
            "address one by its peer name or paneId"
        )
    if not matches:
        attached_agents = (
            ", ".join(
                peer_label(agent_directory[name]) for name in sorted(agent_directory)
            )
            or "none attached"
        )
        raise PeerRequestFailure(
            f"unknown agent {agent_target!r}; attached agents: {attached_agents}"
        )
    return matches[0]["endpoint"].rstrip("/")


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
