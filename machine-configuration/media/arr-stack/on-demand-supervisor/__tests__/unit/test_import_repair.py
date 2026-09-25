import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "scripts" / "on_demand_supervisor")
)

import import_repair


@pytest.fixture
def download():
    return {
        "downloadId": "abc",
        "outputPath": "/data/torrents/movie.mkv",
        "status": "completed",
        "trackedDownloadState": "importBlocked",
        "sizeleft": 0,
    }


@pytest.fixture
def candidate(download):
    return {
        "path": download["outputPath"],
        "downloadId": "ABC",
        "movie": {"id": 12, "monitored": True, "hasFile": False},
        "series": {"id": 4, "monitored": True},
        "episodes": [{"id": 8, "seriesId": 4, "monitored": True, "hasFile": False}],
        "quality": {"quality": {"id": 3}},
        "languages": [{"id": 1}],
        "rejections": [],
    }


@pytest.mark.parametrize("application", ["radarr", "sonarr"])
def test_verified_missing_media_can_be_imported(application, download, candidate):
    result = import_repair.import_file(application, download, [candidate])
    assert result["downloadId"] == "abc"
    assert result["path"] == download["outputPath"]
    if application == "sonarr":
        assert result["episodeIds"] == [8]
    else:
        assert result["movieId"] == 12


@pytest.mark.parametrize(
    "field,value",
    [
        ("rejections", [{"reason": "Unknown movie"}]),
        ("movie", {}),
        ("movie", {"id": 12, "monitored": False, "hasFile": False}),
        ("movie", {"id": 12, "monitored": True, "hasFile": True}),
        ("downloadId", "different"),
        ("path", "/data/media/movie.mkv"),
        ("quality", None),
        ("languages", []),
    ],
)
def test_rejected_unknown_deleted_or_existing_media_is_not_forced(
    download, candidate, field, value
):
    candidate[field] = value
    assert import_repair.import_file("radarr", download, [candidate]) is None


def test_multiple_candidates_and_episode_mismatches_are_rejected(download, candidate):
    assert import_repair.import_file("radarr", download, [candidate, candidate]) is None
    candidate["episodes"][0]["seriesId"] = 99
    assert import_repair.import_file("sonarr", download, [candidate]) is None
    candidate["episodes"] = []
    assert import_repair.import_file("sonarr", download, [candidate]) is None


def test_path_traversal_is_rejected(download, candidate):
    candidate["path"] = download["outputPath"] = "/data/torrents/../media/movie.mkv"
    assert import_repair.import_file("radarr", download, [candidate]) is None


def test_repair_submits_copy_without_search_or_delete(monkeypatch, download, candidate):
    calls = []

    def request(base_url, api_key, path, payload=None):
        calls.append((path, payload))
        if path.startswith("queue?"):
            return {"records": [download]}
        if path.startswith("manualimport?"):
            return [candidate]
        if payload is None:
            return []
        return {"id": 42}

    monkeypatch.setattr(import_repair, "request_json", request)
    import_repair.repair_application("radarr", "url", "key", 900, False)
    assert calls[-1][0] == "command"
    assert calls[-1][1]["importMode"] == "copy"
    assert calls[-1][1]["name"] == "ManualImport"
    calls.clear()
    import_repair.repair_application("radarr", "url", "key", 900, True)
    assert all(payload is None for _, payload in calls)


def test_work_is_bounded_rotates_and_excludes_incomplete_downloads(
    monkeypatch, download
):
    records = [dict(download, downloadId=str(index)) for index in range(5)]
    records.append(dict(download, downloadId="incomplete", status="downloading"))
    paths = []

    def request(base_url, api_key, path, payload=None):
        if path.startswith("queue?"):
            return {"records": records}
        if path == "command":
            return []
        paths.append(path)
        return []

    monkeypatch.setattr(import_repair, "request_json", request)
    for now in (0, 900, 1800):
        import_repair.repair_application("radarr", "url", "key", now, False)
    assert len(paths) == 6
    assert len(set(paths)) == 5
    assert all("incomplete" not in path for path in paths)


def test_interval_and_unavailable_application_isolation(monkeypatch, tmp_path):
    configuration = {"state_file_path": str(tmp_path / "activity")}
    for application in ("radarr", "sonarr"):
        configuration[application + "_url"] = application
        configuration[application + "_config_file"] = application
    monkeypatch.setattr(
        import_repair, "read_arr_api_key_from_config_xml", lambda path: "key"
    )
    calls = []

    def repair(application, *args):
        calls.append(application)
        if application == "radarr":
            raise OSError("unreachable")

    monkeypatch.setattr(import_repair, "repair_application", repair)
    import_repair.maybe_repair_blocked_imports(configuration, 1000, False)
    import_repair.maybe_repair_blocked_imports(configuration, 1001, False)
    assert calls == ["radarr", "sonarr"]
    import_repair.maybe_repair_blocked_imports(configuration, 1900, False)
    assert calls == ["radarr", "sonarr"] * 2


def test_dry_run_does_not_write_state(monkeypatch, tmp_path):
    configuration = {"state_file_path": str(tmp_path / "activity")}
    for application in ("radarr", "sonarr"):
        configuration[application + "_url"] = application
        configuration[application + "_config_file"] = application
    monkeypatch.setattr(
        import_repair, "read_arr_api_key_from_config_xml", lambda path: "key"
    )
    monkeypatch.setattr(import_repair, "repair_application", lambda *args: None)
    import_repair.maybe_repair_blocked_imports(configuration, 1000, True)
    assert list(tmp_path.iterdir()) == []


def test_running_import_prevents_duplicate_submission(monkeypatch, download):
    calls = []

    def request(base_url, api_key, path, payload=None):
        calls.append(path)
        if path.startswith("queue?"):
            return {"records": [download]}
        return [{"name": "ManualImport", "status": "started"}]

    monkeypatch.setattr(import_repair, "request_json", request)
    import_repair.repair_application("radarr", "url", "key", 900, False)
    assert len(calls) == 2


@pytest.mark.parametrize(
    "field,value", [("hasFile", True), ("monitored", False), ("id", None)]
)
def test_existing_or_unmonitored_episode_is_not_replaced(
    download, candidate, field, value
):
    candidate["episodes"][0][field] = value
    assert import_repair.import_file("sonarr", download, [candidate]) is None
