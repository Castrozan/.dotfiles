import base64
import json
import threading
from http.server import HTTPServer
from http.client import HTTPConnection
from urllib.parse import urlsplit

import pytest

from download_cleanup.domain import Media
from download_cleanup.ledger import Ledger
from download_cleanup.server import webhook_handler


@pytest.fixture
def endpoint(tmp_path):
    ledger = Ledger(tmp_path / "cleanup.sqlite")
    server = HTTPServer(
        ("127.0.0.1", 0), webhook_handler(ledger, "test-secret", threading.Event())
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}", ledger
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def post(endpoint, payload, authenticated=True):
    headers = {"Content-Type": "application/json"}
    if authenticated:
        headers["Authorization"] = (
            "Basic " + base64.b64encode(b"cleanup:test-secret").decode()
        )
    address = urlsplit(endpoint)
    connection = HTTPConnection(address.hostname, address.port, timeout=2)
    try:
        connection.request("POST", "/sonarr", json.dumps(payload).encode(), headers)
        return connection.getresponse().status
    finally:
        connection.close()


def test_native_grab_and_delete_are_persisted_before_acknowledgement(endpoint):
    url, ledger = endpoint
    series = {
        "id": 12,
        "tvdbId": 1234,
        "title": "Example",
        "path": "/data/media/tv/Example",
    }
    assert (
        post(
            url,
            {
                "eventType": "Grab",
                "series": series,
                "downloadClientType": "qBittorrent",
                "downloadId": "A" * 40,
            },
        )
        == 200
    )
    assert (
        post(url, {"eventType": "SeriesDelete", "series": series, "deletedFiles": True})
        == 200
    )
    media = Media("sonarr", 12, 1234, "Example", series["path"])
    assert ledger.downloads(media) == [("a" * 40, "")]
    assert ledger.pending() == [media]


def test_unauthenticated_deletion_is_rejected(endpoint):
    url, ledger = endpoint
    assert (
        post(
            url,
            {"eventType": "SeriesDelete", "deletedFiles": True},
            authenticated=False,
        )
        == 401
    )
    assert ledger.pending() == []


def test_test_event_and_record_only_deletion_do_not_enqueue(endpoint):
    url, ledger = endpoint
    assert post(url, {"eventType": "Test"}) == 200
    assert post(url, {"eventType": "SeriesDelete", "deletedFiles": False}) == 200
    assert ledger.pending() == []


def test_malformed_deletion_is_rejected(endpoint):
    url, ledger = endpoint
    assert (
        post(url, {"eventType": "SeriesDelete", "deletedFiles": True, "series": {}})
        == 400
    )
    assert ledger.pending() == []
