import json
import sys
from pathlib import Path

SUPERVISOR_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "on_demand_supervisor"
)
sys.path.insert(0, str(SUPERVISOR_PACKAGE_DIRECTORY_PATH))

import missing_search_sweep

RADARR_ENDPOINT = ("http://radarr", "radarr-key")
SONARR_ENDPOINT = ("http://sonarr", "sonarr-key")


def build_http_router(responses, recorded_posts):
    def http_request(method, url, headers, timeout_seconds=15, body=None):
        if method == "POST":
            recorded_posts.append((url, json.loads(body)))
            return 201, ""
        if "indexerstatus" in url:
            return responses["indexerstatus"]
        if url.endswith("/api/v3/indexer"):
            return responses["indexer"]
        if "wanted/missing" in url:
            return responses["missing"]
        if "queue" in url:
            return responses["queue"]
        raise AssertionError(f"unexpected request {method} {url}")

    return http_request


def test_active_indexer_count_subtracts_backed_off_indexers(monkeypatch):
    responses = {
        "indexer": (
            200,
            json.dumps(
                [
                    {"id": 1, "enableAutomaticSearch": True},
                    {"id": 2, "enableAutomaticSearch": True},
                    {"id": 3, "enableAutomaticSearch": True},
                    {"id": 4, "enableAutomaticSearch": False},
                ]
            ),
        ),
        "indexerstatus": (
            200,
            json.dumps([{"indexerId": 2, "disabledTill": "2999-01-01T00:00:00Z"}]),
        ),
    }
    monkeypatch.setattr(
        missing_search_sweep, "http_request", build_http_router(responses, [])
    )
    assert missing_search_sweep.active_indexer_count("http://radarr", "k", 1000.0) == 2


def test_active_indexer_count_is_none_when_app_unreachable(monkeypatch):
    monkeypatch.setattr(
        missing_search_sweep,
        "http_request",
        lambda method, url, headers, timeout_seconds=15, body=None: (500, ""),
    )
    assert (
        missing_search_sweep.active_indexer_count("http://radarr", "k", 1000.0) is None
    )


def test_sweep_app_defers_and_sends_nothing_when_no_indexers_active(monkeypatch):
    recorded_posts = []
    responses = {
        "indexer": (200, json.dumps([{"id": 1, "enableAutomaticSearch": True}])),
        "indexerstatus": (
            200,
            json.dumps([{"indexerId": 1, "disabledTill": "2999-01-01T00:00:00Z"}]),
        ),
    }
    monkeypatch.setattr(
        missing_search_sweep,
        "http_request",
        build_http_router(responses, recorded_posts),
    )
    outcome = missing_search_sweep.sweep_app(
        RADARR_ENDPOINT, "MoviesSearch", "movieIds", "movieId", 1000.0, False
    )
    assert outcome == "deferred"
    assert recorded_posts == []


def test_sweep_app_searches_missing_items_not_already_queued(monkeypatch):
    recorded_posts = []
    responses = {
        "indexer": (200, json.dumps([{"id": 1, "enableAutomaticSearch": True}])),
        "indexerstatus": (200, json.dumps([])),
        "missing": (
            200,
            json.dumps({"records": [{"id": 10}, {"id": 11}, {"id": 12}]}),
        ),
        "queue": (200, json.dumps({"records": [{"movieId": 11}]})),
    }
    monkeypatch.setattr(
        missing_search_sweep,
        "http_request",
        build_http_router(responses, recorded_posts),
    )
    outcome = missing_search_sweep.sweep_app(
        RADARR_ENDPOINT, "MoviesSearch", "movieIds", "movieId", 1000.0, False
    )
    assert outcome == "swept"
    assert recorded_posts == [
        ("http://radarr/api/v3/command", {"name": "MoviesSearch", "movieIds": [10, 12]})
    ]


def test_sweep_app_sends_nothing_when_every_missing_item_is_queued(monkeypatch):
    recorded_posts = []
    responses = {
        "indexer": (200, json.dumps([{"id": 1, "enableAutomaticSearch": True}])),
        "indexerstatus": (200, json.dumps([])),
        "missing": (200, json.dumps({"records": [{"id": 10}]})),
        "queue": (200, json.dumps({"records": [{"movieId": 10}]})),
    }
    monkeypatch.setattr(
        missing_search_sweep,
        "http_request",
        build_http_router(responses, recorded_posts),
    )
    outcome = missing_search_sweep.sweep_app(
        RADARR_ENDPOINT, "MoviesSearch", "movieIds", "movieId", 1000.0, False
    )
    assert outcome == "swept"
    assert recorded_posts == []


def test_run_missing_search_sweep_reports_false_when_both_apps_defer(monkeypatch):
    monkeypatch.setattr(
        missing_search_sweep,
        "sweep_app",
        lambda *args, **kwargs: "deferred",
    )
    assert (
        missing_search_sweep.run_missing_search_sweep(
            RADARR_ENDPOINT, SONARR_ENDPOINT, 1000.0, False
        )
        is False
    )


def test_run_missing_search_sweep_reports_true_when_one_app_sweeps(monkeypatch):
    outcomes = iter(["deferred", "swept"])
    monkeypatch.setattr(
        missing_search_sweep,
        "sweep_app",
        lambda *args, **kwargs: next(outcomes),
    )
    assert (
        missing_search_sweep.run_missing_search_sweep(
            RADARR_ENDPOINT, SONARR_ENDPOINT, 1000.0, False
        )
        is True
    )
