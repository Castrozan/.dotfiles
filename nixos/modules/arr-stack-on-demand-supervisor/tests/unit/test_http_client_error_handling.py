import io
import sys
import urllib.error
from pathlib import Path

SUPERVISOR_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "on_demand_supervisor"
)
sys.path.insert(0, str(SUPERVISOR_PACKAGE_DIRECTORY_PATH))

import http_client


def test_http_request_returns_status_and_body_on_http_error(monkeypatch):
    def raise_unauthorized(request, timeout=15):
        raise urllib.error.HTTPError(
            request.full_url,
            401,
            "Unauthorized",
            {},
            io.BytesIO(b'{"error":"bad key"}'),
        )

    monkeypatch.setattr(http_client.urllib.request, "urlopen", raise_unauthorized)
    status_code, body = http_client.http_request("GET", "http://jellyseerr/api", {})
    assert status_code == 401
    assert "bad key" in body


def test_http_request_encodes_str_body_and_preserves_method(monkeypatch):
    captured = {}

    class FakeResponse:
        status = 201

        def read(self):
            return b""

        def __enter__(self):
            return self

        def __exit__(self, *exception_info):
            return False

    def capture(request, timeout=15):
        captured["data"] = request.data
        captured["method"] = request.get_method()
        return FakeResponse()

    monkeypatch.setattr(http_client.urllib.request, "urlopen", capture)
    status_code, body = http_client.http_request(
        "POST",
        "http://radarr/api/v3/command",
        {"Content-Type": "application/json"},
        body='{"name":"MoviesSearch"}',
    )
    assert status_code == 201
    assert captured["data"] == b'{"name":"MoviesSearch"}'
    assert captured["method"] == "POST"
