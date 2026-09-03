import json
import sys
from pathlib import Path

SUPERVISOR_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "on_demand_supervisor"
)
sys.path.insert(0, str(SUPERVISOR_PACKAGE_DIRECTORY_PATH))

import missing_search_sweep
import missing_search_api

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
        if url.endswith("/api/v3/series"):
            return responses["series"]
        if "queue" in url:
            return responses["queue"]
        raise AssertionError(f"unexpected request {method} {url}")

    return http_request


def build_responses(episode_file_count, missing_records, downloads=None):
    return {
        "indexer": (200, json.dumps([{"id": 1, "enableAutomaticSearch": True}])),
        "indexerstatus": (200, json.dumps([])),
        "missing": (200, json.dumps({"records": missing_records})),
        "series": (
            200,
            json.dumps(
                [
                    {
                        "id": 50,
                        "seasons": [
                            {
                                "seasonNumber": 1,
                                "statistics": {
                                    "episodeCount": 2,
                                    "episodeFileCount": episode_file_count,
                                },
                            }
                        ],
                    }
                ]
            ),
        ),
        "queue": (200, json.dumps({"records": downloads or []})),
    }


def test_sonarr_sweep_searches_a_complete_missing_season_as_one_pack(monkeypatch):
    recorded_posts = []
    responses = build_responses(
        0,
        [
            {"id": 10, "seriesId": 50, "seasonNumber": 1},
            {"id": 11, "seriesId": 50, "seasonNumber": 1},
        ],
    )
    monkeypatch.setattr(
        missing_search_api,
        "http_request",
        build_http_router(responses, recorded_posts),
    )
    outcome = missing_search_sweep.sweep_sonarr(SONARR_ENDPOINT, 1000.0, False)
    assert outcome == "swept"
    assert recorded_posts == [
        (
            "http://sonarr/api/v3/command",
            {"name": "SeasonSearch", "seriesId": 50, "seasonNumber": 1},
        )
    ]


def test_sonarr_sweep_keeps_episode_search_for_a_partially_downloaded_season(
    monkeypatch,
):
    recorded_posts = []
    responses = build_responses(
        1,
        [{"id": 10, "seriesId": 50, "seasonNumber": 1}],
    )
    monkeypatch.setattr(
        missing_search_api,
        "http_request",
        build_http_router(responses, recorded_posts),
    )
    outcome = missing_search_sweep.sweep_sonarr(SONARR_ENDPOINT, 1000.0, False)
    assert outcome == "swept"
    assert recorded_posts == [
        (
            "http://sonarr/api/v3/command",
            {"name": "EpisodeSearch", "episodeIds": [10]},
        )
    ]


def test_sonarr_sweep_does_not_repeat_a_complete_season_already_downloading(
    monkeypatch,
):
    recorded_posts = []
    responses = build_responses(
        0,
        [
            {"id": 10, "seriesId": 50, "seasonNumber": 1},
            {"id": 11, "seriesId": 50, "seasonNumber": 1},
        ],
        [{"seriesId": 50}],
    )
    monkeypatch.setattr(
        missing_search_api,
        "http_request",
        build_http_router(responses, recorded_posts),
    )
    outcome = missing_search_sweep.sweep_sonarr(SONARR_ENDPOINT, 1000.0, False)
    assert outcome == "swept"
    assert recorded_posts == []
