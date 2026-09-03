import json
import sys
import urllib.error
from pathlib import Path

SUPERVISOR_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "on_demand_supervisor"
)
sys.path.insert(0, str(SUPERVISOR_PACKAGE_DIRECTORY_PATH))

import missing_search_sweep
import missing_search_api

RADARR_ENDPOINT = ("http://radarr", "radarr-key")


def raise_connection_refused(method, url, headers, timeout_seconds=15, body=None):
    raise urllib.error.URLError("connection refused")


def test_active_indexer_count_is_none_when_connection_raises(monkeypatch):
    monkeypatch.setattr(missing_search_api, "http_request", raise_connection_refused)
    assert missing_search_api.active_indexer_count("http://radarr", "k", 1000.0) is None


def test_monitored_missing_records_is_none_when_connection_raises(monkeypatch):
    monkeypatch.setattr(missing_search_api, "http_request", raise_connection_refused)
    assert missing_search_api.monitored_missing_records("http://radarr", "k") is None


def test_queued_records_is_none_when_connection_raises(monkeypatch):
    monkeypatch.setattr(missing_search_api, "http_request", raise_connection_refused)
    assert missing_search_api.queued_records("http://radarr", "k") is None


def test_sweep_app_defers_when_search_post_connection_raises(monkeypatch):
    def http_request(method, url, headers, timeout_seconds=15, body=None):
        if method == "POST":
            raise urllib.error.URLError("connection reset")
        if "indexerstatus" in url:
            return 200, json.dumps([])
        if url.endswith("/api/v3/indexer"):
            return 200, json.dumps([{"id": 1, "enableAutomaticSearch": True}])
        if "wanted/missing" in url:
            return 200, json.dumps({"records": [{"id": 10}]})
        if "queue" in url:
            return 200, json.dumps({"records": []})
        raise AssertionError(f"unexpected request {method} {url}")

    monkeypatch.setattr(missing_search_api, "http_request", http_request)
    outcome = missing_search_sweep.sweep_app(
        RADARR_ENDPOINT, "MoviesSearch", "movieIds", "movieId", 1000.0, False
    )
    assert outcome == "deferred"
