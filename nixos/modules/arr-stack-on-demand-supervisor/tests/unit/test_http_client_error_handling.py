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
