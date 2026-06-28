import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from mem0_mcp_remote_rest_backend import (
    RemoteMemoryServiceUnavailable,
    RemoteRestMemoryBackend,
)


class StubMemoryServiceHandler(BaseHTTPRequestHandler):
    health_status_code = 200

    def log_message(self, *args):
        pass

    def _send(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/health"):
            self._send(self.health_status_code, {"status": "ok"})
            return
        if self.path.startswith("/memories"):
            self._send(200, {"results": [{"id": "1", "memory": "listed"}]})
            return
        self._send(404, {})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        if self.path == "/memories":
            self._send(200, {"results": [{"id": "1", "memory": "added"}]})
            return
        if self.path == "/search":
            self._send(200, {"results": [{"id": "1", "memory": "found"}]})
            return
        self._send(404, {})

    def do_DELETE(self):
        StubMemoryServiceHandler.last_delete_path = self.path
        self._send(200, {"message": "deleted"})


@pytest.fixture
def running_stub_service():
    StubMemoryServiceHandler.health_status_code = 200
    server = HTTPServer(("127.0.0.1", 0), StubMemoryServiceHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()


def test_is_healthy_true_when_health_returns_2xx(running_stub_service):
    backend = RemoteRestMemoryBackend(running_stub_service)
    assert backend.is_healthy() is True


def test_is_healthy_false_when_health_returns_503(running_stub_service):
    StubMemoryServiceHandler.health_status_code = 503
    backend = RemoteRestMemoryBackend(running_stub_service)
    assert backend.is_healthy() is False


def test_add_posts_messages_payload(running_stub_service):
    backend = RemoteRestMemoryBackend(running_stub_service)
    result = backend.add("remember this", "lucas")
    assert result["results"][0]["memory"] == "added"


def test_search_extracts_results_list(running_stub_service):
    backend = RemoteRestMemoryBackend(running_stub_service)
    assert backend.search("q", "lucas", 5) == [{"id": "1", "memory": "found"}]


def test_list_memories_extracts_results(running_stub_service):
    backend = RemoteRestMemoryBackend(running_stub_service)
    assert backend.list_memories("lucas") == [{"id": "1", "memory": "listed"}]


def test_delete_hits_percent_encoded_memory_path(running_stub_service):
    StubMemoryServiceHandler.last_delete_path = None
    backend = RemoteRestMemoryBackend(running_stub_service)
    result = backend.delete("id with/slash")
    assert result["message"] == "deleted"
    assert StubMemoryServiceHandler.last_delete_path == "/memories/id%20with/slash"


def test_unreachable_host_raises_service_unavailable():
    backend = RemoteRestMemoryBackend("http://127.0.0.1:1", request_timeout_seconds=1.0)
    with pytest.raises(RemoteMemoryServiceUnavailable):
        backend.add("x", "lucas")
