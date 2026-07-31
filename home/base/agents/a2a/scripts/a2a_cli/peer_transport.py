from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_PEER_REGISTRY_PATH = Path.home() / ".claude" / "a2a" / "peers.json"
TERMINAL_TASK_STATES = frozenset({"completed", "canceled", "failed"})
REACHABILITY_PROBE_TIMEOUT_SECONDS = 2.0
TASK_REQUEST_TIMEOUT_SECONDS = 10.0
DEFAULT_ANSWER_TIMEOUT_SECONDS = 900.0
POLL_INTERVAL_SECONDS = 2.0


class PeerRequestFailure(Exception):
    pass


def load_peer_registry(registry_path: Path) -> dict:
    if not registry_path.is_file():
        return {}
    try:
        return json.loads(registry_path.read_text(encoding="utf-8")).get("peers", {})
    except (json.JSONDecodeError, UnicodeDecodeError) as parse_failure:
        raise PeerRequestFailure(
            f"peer registry {registry_path} is not readable JSON: {parse_failure}"
        ) from parse_failure


def resolve_peer_endpoint(peer_registry: dict, agent_name: str) -> str:
    peer = peer_registry.get(agent_name)
    if peer is None:
        declared_peer_names = ", ".join(sorted(peer_registry)) or "none declared"
        raise PeerRequestFailure(
            f"unknown peer {agent_name!r}; declared peers: {declared_peer_names}"
        )
    return peer["endpoint"].rstrip("/")


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


def peer_is_reachable(endpoint: str) -> bool:
    try:
        status_code, _ = request_peer_json(
            "GET",
            f"{endpoint}/health",
            timeout_seconds=REACHABILITY_PROBE_TIMEOUT_SECONDS,
        )
    except PeerRequestFailure:
        return False
    return status_code == 200


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
