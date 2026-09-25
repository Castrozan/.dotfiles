import sys
from pathlib import Path

import pytest

sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "scripts" / "on_demand_supervisor")
)

from import_repair.history import grabbed_identity, reprocess_from_history


def grabbed(**changes):
    return {
        "downloadId": "ABC",
        "eventType": "grabbed",
        "movieId": 12,
        "seriesId": 4,
        "episodeId": 8,
        **changes,
    }


@pytest.mark.parametrize(
    "application,expected", [("sonarr", (4, 8)), ("radarr", (12,))]
)
def test_grabbed_identity_uses_exact_hash(application, expected):
    assert grabbed_identity(application, "abc", {"records": [grabbed()]}) == expected


@pytest.mark.parametrize(
    "records",
    [
        [],
        [grabbed(downloadId="other")],
        [grabbed(eventType="downloadFailed")],
        [grabbed(movieId=None)],
        [grabbed(), grabbed(movieId=13)],
    ],
)
def test_unproven_or_conflicting_history_is_not_matched(records):
    assert grabbed_identity("radarr", "abc", {"records": records}) is None


def test_truncated_history_is_not_used():
    assert (
        grabbed_identity("radarr", "abc", {"totalRecords": 101, "records": [grabbed()]})
        is None
    )


@pytest.mark.parametrize("application", ["sonarr", "radarr"])
def test_history_reprocesses_only_a_still_wanted_missing_file(application):
    candidate = {
        "path": "/data/torrents/file.mkv",
        "downloadId": "abc",
        "rejections": [{"reason": "Unknown Movie"}],
    }
    record = {"outputPath": candidate["path"], "downloadId": "abc"}
    calls = []

    def request(path, payload=None):
        calls.append((path, payload))
        if path.startswith("history?"):
            return {"records": [grabbed()]}
        if path == "manualimport":
            return [{**payload[0], "rejections": []}]
        return {
            "id": 12,
            "monitored": True,
            "hasFile": False,
            "seriesId": 4,
            "seasonNumber": 1,
        }

    result = reprocess_from_history(application, record, [candidate], request)
    assert result[0]["rejections"] == []
    payload = calls[-1][1][0]
    if application == "sonarr":
        assert payload["seriesId"] == 4
        assert payload["episodeIds"] == [8]
    else:
        assert payload["movieId"] == 12


@pytest.mark.parametrize(
    "application,media",
    [
        ("radarr", {"monitored": False, "hasFile": False}),
        ("radarr", {"monitored": True, "hasFile": True}),
        ("sonarr", {"monitored": True, "hasFile": True, "seriesId": 4}),
        ("sonarr", {"monitored": True, "hasFile": False, "seriesId": 99}),
    ],
)
def test_reprocessing_preserves_deleted_unmonitored_and_existing_media(
    application, media
):
    candidate = {
        "path": "/data/torrents/file.mkv",
        "downloadId": "abc",
        "rejections": [{"reason": "Unknown Movie"}],
    }
    record = {"outputPath": candidate["path"], "downloadId": "abc"}

    def request(path, payload=None):
        assert payload is None
        return {"records": [grabbed()]} if path.startswith("history?") else media

    assert reprocess_from_history(application, record, [candidate], request) == [
        candidate
    ]


@pytest.mark.parametrize(
    "reason", ["Not enough free space", "File is a sample", "Quality is not wanted"]
)
def test_other_rejections_never_use_history(reason):
    candidate = {"rejections": [{"reason": reason}]}

    def unexpected_request(*args):
        pytest.fail("Unrelated rejection must not be overridden")

    assert reprocess_from_history("radarr", {}, [candidate], unexpected_request) == [
        candidate
    ]
