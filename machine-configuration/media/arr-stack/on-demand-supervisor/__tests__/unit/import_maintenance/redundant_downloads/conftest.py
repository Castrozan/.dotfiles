import copy
from functools import partial
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

sys.path.insert(
    0, str(Path(__file__).resolve().parents[4] / "scripts" / "on_demand_supervisor")
)

import import_repair.redundant_downloads.cleanup as cleanup


@pytest.fixture
def completed_pack():
    reason = "Not an upgrade for existing episode file(s). Existing quality: Bluray-1080p. New Quality WEBDL-1080p."
    record = {
        "id": 17,
        "downloadId": "a" * 40,
        "seriesId": 31,
        "status": "completed",
        "trackedDownloadState": "importBlocked",
        "sizeleft": 0,
        "outputPath": "/data/torrents/Solo.Leveling.S02",
        "statusMessages": [{"messages": [reason] * 13}],
    }
    episodes = [
        {"id": number, "seriesId": 31, "hasFile": True, "episodeFileId": 100 + number}
        for number in range(1, 14)
    ]
    candidates = [
        {
            "path": f"{record['outputPath']}/S02E{episode['id']:02d}.mkv",
            "downloadId": record["downloadId"].upper(),
            "series": {"id": 31},
            "episodes": [copy.deepcopy(episode)],
            "size": 1000,
            "rejections": [{"reason": reason, "type": "permanent"}],
        }
        for episode in episodes
    ]
    files = [
        {
            "id": episode["episodeFileId"],
            "seriesId": 31,
            "path": f"/data/media/tv/Solo Leveling/Season 2/S02E{episode['id']:02d}.mkv",
            "size": 2000,
        }
        for episode in episodes
    ]
    directories = {
        record["outputPath"] + "/": {
            "directories": [],
            "files": [
                {"path": candidate["path"], "size": 1000, "type": "file"}
                for candidate in candidates
            ],
        },
        "/data/media/tv/Solo Leveling/Season 2/": {
            "directories": [],
            "files": [{**file, "type": "file"} for file in files],
        },
    }
    return record, candidates, episodes, files, directories


def run_cleanup(monkeypatch, completed_pack, dry_run=False, delete_status=200):
    record, candidates, episodes, files, directories = completed_pack
    calls = []

    def request(method, url, headers, timeout_seconds, **kwargs):
        calls.append((method, url, timeout_seconds))
        route = urlsplit(url)
        query = parse_qs(route.query)
        if method == "DELETE":
            assert route.path == "/api/v3/queue/17"
            assert query == {
                "removeFromClient": ["true"],
                "blocklist": ["false"],
                "skipRedownload": ["true"],
            }
            return delete_status, ""
        if route.path.endswith("/command"):
            value = directories.get("commands", [])
        elif route.path.endswith("/manualimport"):
            assert query["filterExistingFiles"] == ["false"]
            value = candidates
        elif route.path.endswith("/episode"):
            value = episodes
        elif route.path.endswith("/episodefile"):
            value = files
        elif route.path.endswith("/filesystem"):
            value = directories[query["path"][0]]
        else:
            raise AssertionError(url)
        return 200, json.dumps(value)

    monkeypatch.setattr(cleanup, "http_request", request)
    result = cleanup.remove_redundant_download("http://sonarr", "key", record, dry_run)
    return result, calls


@pytest.fixture(name="run_cleanup")
def cleanup_runner(monkeypatch, completed_pack):
    return partial(run_cleanup, monkeypatch, completed_pack)
