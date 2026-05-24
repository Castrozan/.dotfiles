import json
import socket
import threading
import time
import urllib.error
import urllib.request

from a2a_server.a2a_server import run_a2a_server_blocking
from a2a_server.agent_card import build_agent_card_from_environment
from a2a_server.backends.subprocess_backend import SubprocessAgentBackend


def _pick_free_local_port() -> int:
    probe_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe_socket.bind(("127.0.0.1", 0))
    port = probe_socket.getsockname()[1]
    probe_socket.close()
    return port


def _wait_for_health_endpoint(
    server_base_url: str, total_wait_budget_seconds: float = 5.0
) -> None:
    deadline_epoch_seconds = time.time() + total_wait_budget_seconds
    while time.time() < deadline_epoch_seconds:
        try:
            with urllib.request.urlopen(
                f"{server_base_url}/health", timeout=1
            ) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, ConnectionError):
            pass
        time.sleep(0.05)
    raise RuntimeError(
        f"health endpoint at {server_base_url}/health did not come up in time"
    )


def _http_get_json(url: str) -> tuple[int, dict]:
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as http_error:
        return http_error.code, json.loads(http_error.read().decode("utf-8"))


def _http_post_json(url: str, payload: dict) -> tuple[int, dict]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as http_error:
        return http_error.code, json.loads(http_error.read().decode("utf-8"))


class _ServerThreadHandle:
    def __init__(
        self,
        server_thread: threading.Thread,
        backend: SubprocessAgentBackend,
        port: int,
    ) -> None:
        self.server_thread = server_thread
        self.backend = backend
        self.port = port
        self.base_url = f"http://127.0.0.1:{port}"


def _start_server_in_background_thread(command_argv: list[str]) -> _ServerThreadHandle:
    port = _pick_free_local_port()
    backend = SubprocessAgentBackend(command_argv=command_argv)
    agent_card = build_agent_card_from_environment(
        agent_name="test-agent",
        description="test fixture",
        endpoint_url=f"http://127.0.0.1:{port}",
    )

    def _serve_until_shutdown():
        run_a2a_server_blocking(
            host="127.0.0.1",
            port=port,
            agent_card=agent_card,
            agent_backend=backend,
        )

    server_thread = threading.Thread(target=_serve_until_shutdown, daemon=True)
    server_thread.start()
    handle = _ServerThreadHandle(
        server_thread=server_thread, backend=backend, port=port
    )
    _wait_for_health_endpoint(handle.base_url)
    return handle


class TestA2AServer:
    def test_agent_card_endpoint_returns_serialized_card(self):
        handle = _start_server_in_background_thread(["bash", "-c", "sleep 5"])
        try:
            status, payload = _http_get_json(
                f"{handle.base_url}/.well-known/agent.json"
            )
            assert status == 200
            assert payload["name"] == "test-agent"
            assert payload["url"] == handle.base_url
        finally:
            handle.backend.stop()

    def test_submit_task_returns_201_with_task_metadata(self):
        handle = _start_server_in_background_thread(["cat"])
        try:
            status, payload = _http_post_json(
                f"{handle.base_url}/tasks/send", {"input": "hello-via-a2a\n"}
            )
            assert status == 201
            assert "id" in payload
            assert payload["state"] in {"submitted", "working"}
        finally:
            handle.backend.stop()

    def test_submit_task_rejects_when_input_field_is_missing(self):
        handle = _start_server_in_background_thread(["bash", "-c", "sleep 5"])
        try:
            status, payload = _http_post_json(f"{handle.base_url}/tasks/send", {})
            assert status == 400
            assert payload["error"] == "missing_input_field"
        finally:
            handle.backend.stop()

    def test_get_task_returns_404_for_unknown_id(self):
        handle = _start_server_in_background_thread(["bash", "-c", "sleep 5"])
        try:
            status, payload = _http_get_json(f"{handle.base_url}/tasks/does-not-exist")
            assert status == 404
            assert payload["error"] == "task_not_found"
        finally:
            handle.backend.stop()

    def test_second_submit_while_active_returns_409_with_existing_task(self):
        handle = _start_server_in_background_thread(["cat"])
        try:
            first_status, first_payload = _http_post_json(
                f"{handle.base_url}/tasks/send", {"input": "first-input\n"}
            )
            assert first_status == 201
            second_status, second_payload = _http_post_json(
                f"{handle.base_url}/tasks/send", {"input": "second-input\n"}
            )
            assert second_status == 409
            assert second_payload["id"] == first_payload["id"]
        finally:
            handle.backend.stop()

    def test_task_output_eventually_reflects_subprocess_response(self):
        handle = _start_server_in_background_thread(["cat"])
        try:
            status, payload = _http_post_json(
                f"{handle.base_url}/tasks/send", {"input": "round-trip-line\n"}
            )
            assert status == 201
            task_id = payload["id"]
            for _ in range(40):
                status, refreshed_payload = _http_get_json(
                    f"{handle.base_url}/tasks/{task_id}"
                )
                if "round-trip-line" in refreshed_payload.get("output", ""):
                    break
                time.sleep(0.05)
            assert "round-trip-line" in refreshed_payload["output"]
        finally:
            handle.backend.stop()
