import sys
import urllib.error
from pathlib import Path

SUPERVISOR_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "on_demand_supervisor"
)
sys.path.insert(0, str(SUPERVISOR_PACKAGE_DIRECTORY_PATH))

import download_activity

ARR_ENDPOINTS = [("http://radarr", "radarr-key"), ("http://sonarr", "sonarr-key")]


def test_queue_active_when_an_endpoint_reports_records(monkeypatch):
    monkeypatch.setattr(
        download_activity,
        "http_request",
        lambda method, url, headers, timeout_seconds=15: (200, '{"totalRecords": 3}'),
    )
    assert download_activity.arr_download_queue_active(ARR_ENDPOINTS) is True


def test_queue_idle_when_every_reached_endpoint_is_empty(monkeypatch):
    monkeypatch.setattr(
        download_activity,
        "http_request",
        lambda method, url, headers, timeout_seconds=15: (200, '{"totalRecords": 0}'),
    )
    assert download_activity.arr_download_queue_active(ARR_ENDPOINTS) is False


def test_queue_assumed_active_when_no_endpoint_is_reachable(monkeypatch):
    def unreachable(method, url, headers, timeout_seconds=15):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(download_activity, "http_request", unreachable)
    assert download_activity.arr_download_queue_active(ARR_ENDPOINTS) is True
