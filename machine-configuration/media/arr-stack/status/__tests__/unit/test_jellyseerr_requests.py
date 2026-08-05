import sys
from pathlib import Path

ARR_STATUS_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "arr_status"
)
sys.path.insert(0, str(ARR_STATUS_PACKAGE_DIRECTORY_PATH))

import jellyseerr_requests


def test_fetch_requests_returns_results(monkeypatch):
    monkeypatch.setattr(
        jellyseerr_requests.arr_http,
        "get_json",
        lambda *a, **k: {"results": [{"id": 1}]},
    )
    assert jellyseerr_requests.fetch_requests("base", "key") == [{"id": 1}]


def test_fetch_requests_falls_back_to_empty_on_none(monkeypatch):
    monkeypatch.setattr(jellyseerr_requests.arr_http, "get_json", lambda *a, **k: None)
    assert jellyseerr_requests.fetch_requests("base", "key") == []


def test_year_from_date_extracts_year_and_tolerates_missing():
    assert jellyseerr_requests.year_from_date("2018-10-02") == "2018"
    assert jellyseerr_requests.year_from_date(None) is None
    assert jellyseerr_requests.year_from_date("") is None


def test_resolve_media_title_uses_name_for_tv(monkeypatch):
    monkeypatch.setattr(
        jellyseerr_requests.arr_http,
        "get_json",
        lambda base, key, path: {"name": "Slime", "firstAirDate": "2018-10-02"},
    )
    title, year = jellyseerr_requests.resolve_media_title("b", "k", "tv", 1)
    assert title == "Slime"
    assert year == "2018"


def test_resolve_media_title_uses_title_for_movie(monkeypatch):
    monkeypatch.setattr(
        jellyseerr_requests.arr_http,
        "get_json",
        lambda base, key, path: {"title": "The DUFF", "releaseDate": "2015-02-20"},
    )
    title, year = jellyseerr_requests.resolve_media_title("b", "k", "movie", 1)
    assert title == "The DUFF"
    assert year == "2015"


def test_request_lifecycle_stage_maps_each_state():
    assert (
        jellyseerr_requests.request_lifecycle_stage({"status": 1, "media": {}})
        == "pending-approval"
    )
    assert (
        jellyseerr_requests.request_lifecycle_stage({"status": 3, "media": {}})
        == "declined"
    )
    assert (
        jellyseerr_requests.request_lifecycle_stage(
            {"status": 2, "media": {"status": 5}}
        )
        == "available"
    )
    assert (
        jellyseerr_requests.request_lifecycle_stage(
            {"status": 2, "media": {"status": 4}}
        )
        == "partial"
    )
    assert (
        jellyseerr_requests.request_lifecycle_stage(
            {"status": 2, "media": {"status": 3}}
        )
        == "processing"
    )
