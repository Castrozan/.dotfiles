import sys
from pathlib import Path

ARR_STATUS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_status"
)
sys.path.insert(0, str(ARR_STATUS_PACKAGE_DIRECTORY_PATH))

import urllib.error
from types import SimpleNamespace

import status_assembly

ENDPOINT = SimpleNamespace(base_url="http://arr", api_key="key")


def test_build_snapshot_returns_unreachable_when_endpoint_none():
    snapshot = status_assembly.build_snapshot(None, lambda endpoint: {})
    assert snapshot.reachable is False
    assert snapshot.records == []


def test_build_snapshot_marks_unreachable_on_url_error(monkeypatch):
    monkeypatch.setattr(
        status_assembly.arr_queue,
        "fetch_queue_records",
        lambda endpoint: (_ for _ in ()).throw(urllib.error.URLError("refused")),
    )
    snapshot = status_assembly.build_snapshot(ENDPOINT, lambda endpoint: {})
    assert snapshot.reachable is False


def test_build_snapshot_collects_records_and_index(monkeypatch):
    monkeypatch.setattr(
        status_assembly.arr_queue,
        "fetch_queue_records",
        lambda endpoint: [{"seriesId": 4}],
    )
    snapshot = status_assembly.build_snapshot(ENDPOINT, lambda endpoint: {99: 4})
    assert snapshot.reachable is True
    assert snapshot.records == [{"seriesId": 4}]
    assert snapshot.id_by_external_id == {99: 4}


def test_progress_from_snapshot_none_when_unreachable():
    snapshot = status_assembly.ArrSnapshot(False, [], {})
    assert status_assembly.progress_from_snapshot(snapshot, 99, "seriesId") is None


def test_progress_from_snapshot_none_when_no_id_match():
    snapshot = status_assembly.ArrSnapshot(True, [], {})
    assert status_assembly.progress_from_snapshot(snapshot, 99, "seriesId") is None


def test_progress_from_snapshot_sums_matching_records():
    snapshot = status_assembly.ArrSnapshot(
        True,
        [
            {"seriesId": 4, "size": 100, "sizeleft": 50},
            {"seriesId": 9, "size": 100, "sizeleft": 0},
        ],
        {99: 4},
    )
    progress = status_assembly.progress_from_snapshot(snapshot, 99, "seriesId")
    assert progress["percent"] == 50


def test_progress_for_request_routes_movie_to_radarr():
    radarr = status_assembly.ArrSnapshot(
        True, [{"movieId": 1, "size": 100, "sizeleft": 25}], {10: 1}
    )
    sonarr = status_assembly.ArrSnapshot(True, [], {})
    request_object = {"media": {"mediaType": "movie", "tmdbId": 10}}
    progress = status_assembly.progress_for_request(request_object, radarr, sonarr)
    assert progress["percent"] == 75


def test_build_status_line_tolerating_title_failure_degrades_on_url_error(monkeypatch):
    def raise_url_error(base, key, media_type, tmdb_id):
        raise urllib.error.URLError("tmdb proxy 404")

    monkeypatch.setattr(
        status_assembly.jellyseerr_requests, "resolve_media_title", raise_url_error
    )
    snapshot = status_assembly.ArrSnapshot(False, [], {})
    request_object = {
        "status": 2,
        "media": {"mediaType": "tv", "tmdbId": 55, "tvdbId": 77, "status": 3},
        "requestedBy": {"displayName": "lucas"},
    }
    line = status_assembly.build_status_line_tolerating_title_failure(
        "b", "k", request_object, snapshot, snapshot
    )
    assert line.title == "tmdb:55"
    assert line.stage == "processing"


def test_build_status_line_falls_back_to_tmdb_and_reads_requester(monkeypatch):
    monkeypatch.setattr(
        status_assembly.jellyseerr_requests,
        "resolve_media_title",
        lambda base, key, media_type, tmdb_id: (None, None),
    )
    sonarr = status_assembly.ArrSnapshot(False, [], {})
    radarr = status_assembly.ArrSnapshot(False, [], {})
    request_object = {
        "status": 2,
        "media": {"mediaType": "tv", "tmdbId": 55, "tvdbId": 77, "status": 3},
        "requestedBy": {"displayName": "xamitos"},
    }
    line = status_assembly.build_status_line("b", "k", request_object, radarr, sonarr)
    assert line.title == "tmdb:55"
    assert line.requested_by == "xamitos"
    assert line.stage == "processing"
    assert line.arr_reachable is False
