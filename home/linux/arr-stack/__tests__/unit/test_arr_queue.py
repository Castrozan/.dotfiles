import sys
from pathlib import Path

ARR_STATUS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_status"
)
sys.path.insert(0, str(ARR_STATUS_PACKAGE_DIRECTORY_PATH))

from types import SimpleNamespace

import arr_queue


def endpoint():
    return SimpleNamespace(base_url="http://arr", api_key="key")


def test_fetch_queue_records_falls_back_to_empty(monkeypatch):
    monkeypatch.setattr(arr_queue.arr_http, "get_json", lambda *a, **k: None)
    assert arr_queue.fetch_queue_records(endpoint()) == []


def test_build_radarr_movie_index_maps_tmdb_to_id(monkeypatch):
    monkeypatch.setattr(
        arr_queue.arr_http,
        "get_json",
        lambda *a, **k: [{"tmdbId": 10, "id": 1}, {"tmdbId": 20, "id": 2}],
    )
    assert arr_queue.build_radarr_movie_index(endpoint()) == {10: 1, 20: 2}


def test_build_sonarr_series_index_maps_tvdb_to_id(monkeypatch):
    monkeypatch.setattr(
        arr_queue.arr_http,
        "get_json",
        lambda *a, **k: [{"tvdbId": 99, "id": 4}],
    )
    assert arr_queue.build_sonarr_series_index(endpoint()) == {99: 4}


def test_download_progress_computes_percent_and_bottleneck_eta():
    records = [
        {"size": 100, "sizeleft": 40, "timeleft": "00:05:00"},
        {"size": 100, "sizeleft": 60, "timeleft": "00:09:58"},
    ]
    progress = arr_queue.download_progress_for_records(records)
    assert progress["percent"] == 50
    assert progress["time_left"] == "00:09:58"
    assert progress["record_count"] == 2


def test_download_progress_none_when_no_size():
    assert arr_queue.download_progress_for_records([]) is None
    assert arr_queue.download_progress_for_records([{"size": 0, "sizeleft": 0}]) is None


def test_bottleneck_time_left_none_when_no_records_have_time():
    assert arr_queue.bottleneck_time_left([{"size": 1, "sizeleft": 1}]) is None
