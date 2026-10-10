import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs

import pytest

from download_cleanup.clients import MediaClient, TorrentClient
from download_cleanup.transport import HttpFailure, HttpTransport


class ApplicationHandler(BaseHTTPRequestHandler):
    def reply(self, status, body, cookie=None):
        self.send_response(status)
        self.send_header("Content-Length", str(len(body)))
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/v3/movie/1":
            self.reply(404, b"{}")
        elif self.path == "/api/v3/movie/2":
            self.reply(503, b"{}")
        elif self.headers.get("Cookie") != "SID=valid":
            self.reply(403, b"")
        else:
            self.reply(200, b"[]")

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        fields = parse_qs(self.rfile.read(length).decode())
        self.server.received.append((self.path, fields, self.headers.get("Cookie")))
        if self.path.endswith("/auth/login"):
            self.reply(200, b"Ok.", "SID=valid; HttpOnly; Path=/")
        else:
            self.reply(200, b"")

    def log_message(self, format, *arguments):
        pass


@pytest.fixture
def application():
    server = HTTPServer(("127.0.0.1", 0), ApplicationHandler)
    server.received = []
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}", server
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def test_torrent_login_cookie_and_file_inclusive_deletion(application):
    url, server = application
    client = TorrentClient(url, "admin", "test-secret")
    assert client.list() == []
    client.delete(["a" * 40, "b" * 40])
    assert server.received[-1] == (
        "/api/v2/torrents/delete",
        {"hashes": ["a" * 40 + "|" + "b" * 40], "deleteFiles": ["true"]},
        "SID=valid",
    )


def test_expired_torrent_cookie_reauthenticates(application):
    url, server = application
    client = TorrentClient(url, "admin", "test-secret")
    assert client.list() == []
    client.transport.cookie = "SID=expired"
    assert client.list() == []
    assert len(server.received) == 2


def test_only_not_found_can_report_media_absent(application):
    url, _ = application
    client = MediaClient(url + "/api/v3", "test-key", "radarr")
    assert not client.exists(1)
    with pytest.raises(HttpFailure) as error:
        client.exists(2)
    assert error.value.status == 503


@pytest.mark.parametrize(
    "address", ["file:///etc/passwd", "ftp://localhost", "relative"]
)
def test_non_http_transports_are_rejected(address):
    with pytest.raises(ValueError, match="HTTP"):
        HttpTransport(address, {})
