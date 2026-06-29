import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from mem0_memory_backends import RemoteMemory, RemoteUnavailable


class StubHandler(BaseHTTPRequestHandler):
    health_status_code = 200
    last_delete_path = None

    def log_message(self, *args):
        pass

    def _send(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/health"):
            self._send(self.health_status_code, {"status": "ok"})
        elif self.path.startswith("/memories"):
            self._send(200, {"results": [{"id": "1", "memory": "listed"}]})
        else:
            self._send(404, {})

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", "0")))
        if self.path == "/memories":
            self._send(200, {"results": [{"id": "1", "memory": "added"}]})
        elif self.path == "/search":
            self._send(200, {"results": [{"id": "1", "memory": "found"}]})
        else:
            self._send(404, {})

    def do_DELETE(self):
        StubHandler.last_delete_path = self.path
        self._send(200, {"message": "deleted"})


@pytest.fixture
def stub_url():
    StubHandler.health_status_code = 200
    server = HTTPServer(("127.0.0.1", 0), StubHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    host, port = server.server_address
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()


def test_is_healthy_true_on_2xx(stub_url):
    assert RemoteMemory(stub_url).is_healthy() is True


def test_is_healthy_false_on_503(stub_url):
    StubHandler.health_status_code = 503
    assert RemoteMemory(stub_url).is_healthy() is False


def test_add_search_list_extract_results(stub_url):
    backend = RemoteMemory(stub_url)
    assert backend.add("x", "lucas")["results"][0]["memory"] == "added"
    assert backend.search("q", "lucas", 5) == [{"id": "1", "memory": "found"}]
    assert backend.list_memories("lucas") == [{"id": "1", "memory": "listed"}]


def test_delete_uses_percent_encoded_path(stub_url):
    StubHandler.last_delete_path = None
    assert RemoteMemory(stub_url).delete("id with/slash")["message"] == "deleted"
    assert StubHandler.last_delete_path == "/memories/id%20with/slash"


def test_unreachable_host_raises_remote_unavailable():
    with pytest.raises(RemoteUnavailable):
        RemoteMemory("http://127.0.0.1:1", request_timeout_seconds=1.0).add(
            "x", "lucas"
        )
