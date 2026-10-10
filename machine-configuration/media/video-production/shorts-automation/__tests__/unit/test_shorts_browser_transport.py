import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import pytest

from shorts_browser_pages.transport import create_page


@pytest.fixture
def page_server(monkeypatch):
    monkeypatch.setattr(
        "shorts_browser_pages.transport.read_document",
        lambda path: {"server": {"token": "fixture-credential"}},
    )

    class PageHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers["Content-Length"]))
            self.server.requests.append(
                (self.path, self.headers["Authorization"], json.loads(body))
            )
            self.send_response(self.server.response_status)
            self.end_headers()
            self.wfile.write(b'{"tabId":"owned-tab"}')

        def log_message(self, *arguments):
            pass

    server = HTTPServer(("127.0.0.1", 0), PageHandler)
    server.requests = []
    server.response_status = 200
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


def test_blank_page_creation_authenticates_and_returns_target(page_server):
    assert create_page(f"http://127.0.0.1:{page_server.server_port}") == "owned-tab"
    assert page_server.requests == [
        ("/tab", "Bearer fixture-credential", {"action": "new"})
    ]


def test_failed_creation_rejects_response_without_exposing_token(page_server):
    page_server.response_status = 503
    with pytest.raises(ValueError, match="HTTP 503") as exception:
        create_page(f"http://127.0.0.1:{page_server.server_port}")
    assert "fixture-credential" not in str(exception.value)
