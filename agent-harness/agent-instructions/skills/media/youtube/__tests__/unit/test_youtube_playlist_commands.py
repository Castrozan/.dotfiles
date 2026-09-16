import importlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


@pytest.fixture
def youtube(monkeypatch):
    directory = Path(__file__).resolve().parents[2] / "scripts"
    monkeypatch.syspath_prepend(str(directory))
    service = Mock()
    for name in ("youtube_playlists", "youtube_playlist_items", "youtube_videos"):
        module = importlib.import_module(name)
        monkeypatch.setattr(module, "get_authenticated_service", lambda: service)
    specification = importlib.util.spec_from_file_location(
        "youtube_test_cli", directory / "youtube-cli.py"
    )
    cli = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(cli)
    return SimpleNamespace(service=service, cli=cli)


def invoke(youtube, monkeypatch, arguments):
    monkeypatch.setattr(sys, "argv", ["youtube-cli", *arguments])
    youtube.cli.main()


def test_playlist_listing_and_private_creation(youtube, monkeypatch, capsys):
    playlists = youtube.service.playlists.return_value
    playlists.list.return_value.execute.return_value = {
        "items": [
            {
                "id": "PL1",
                "snippet": {"title": "Music"},
                "contentDetails": {"itemCount": 2},
            }
        ]
    }
    invoke(youtube, monkeypatch, ["playlists"])
    result = json.loads(capsys.readouterr().out)
    assert result == [
        {
            "id": "PL1",
            "title": "Music",
            "description": "",
            "video_count": 2,
            "url": "https://www.youtube.com/playlist?list=PL1",
        }
    ]
    playlists.list.assert_called_once_with(
        part="snippet,contentDetails", mine=True, maxResults=25
    )
    playlists.insert.return_value.execute.return_value = {
        "id": "PL2",
        "snippet": {"title": "New"},
        "status": {"privacyStatus": "private"},
    }
    invoke(youtube, monkeypatch, ["playlist-create", "New", "-d", "Songs"])
    playlists.insert.assert_called_once_with(
        part="snippet,status",
        body={
            "snippet": {"title": "New", "description": "Songs"},
            "status": {"privacyStatus": "private"},
        },
    )
    assert json.loads(capsys.readouterr().out)["privacy"] == "private"


def test_playlist_pagination_respects_limit(youtube, monkeypatch, capsys):
    items = youtube.service.playlistItems.return_value
    item = {
        "id": "item",
        "snippet": {
            "resourceId": {"videoId": "abcdefghijk"},
            "title": "Video",
            "position": 0,
        },
    }
    items.list.return_value.execute.side_effect = [
        {"items": [item], "nextPageToken": "page2"},
        {"items": [item], "nextPageToken": "page3"},
    ]
    invoke(
        youtube,
        monkeypatch,
        ["playlist-list", "https://youtube.com/playlist?list=PL1", "-n", "2"],
    )
    assert len(json.loads(capsys.readouterr().out)) == 2
    assert items.list.call_args_list[0].kwargs == dict(
        part="snippet,contentDetails", playlistId="PL1", maxResults=2, pageToken=None
    )
    assert items.list.call_args_list[1].kwargs["maxResults"] == 1
    assert items.list.call_args_list[1].kwargs["pageToken"] == "page2"
    items.list.return_value.execute.side_effect = [{"items": []}]
    invoke(youtube, monkeypatch, ["playlist-list", "PL1"])
    assert json.loads(capsys.readouterr().out) == []


def test_playlist_mutations_report_each_success_and_failure(
    youtube, monkeypatch, capsys
):
    items = youtube.service.playlistItems.return_value
    items.insert.return_value.execute.side_effect = [
        {"snippet": {"title": "Video", "position": 0}},
        RuntimeError("denied"),
    ]
    invoke(
        youtube,
        monkeypatch,
        ["playlist-add", "PL1", "https://youtu.be/abcdefghijk", "bad-id"],
    )
    results = json.loads(capsys.readouterr().out)
    assert results[0] == {
        "status": "added",
        "video_id": "abcdefghijk",
        "title": "Video",
        "position": 0,
    }
    assert results[1] == {"status": "error", "video_id": "bad-id", "error": "denied"}
    assert (
        items.insert.call_args_list[0].kwargs["body"]["snippet"]["resourceId"][
            "videoId"
        ]
        == "abcdefghijk"
    )
    items.delete.return_value.execute.side_effect = [None, RuntimeError("missing")]
    invoke(youtube, monkeypatch, ["playlist-remove", " item1 ", "item2"])
    results = json.loads(capsys.readouterr().out)
    assert [result["status"] for result in results] == ["removed", "error"]
    assert items.delete.call_args_list[0].kwargs == {"id": "item1"}
    assert results[1]["error"] == "missing"


def test_video_info_and_search_dispatch_preserve_arguments(
    youtube, monkeypatch, capsys
):
    videos = youtube.service.videos.return_value
    videos.list.return_value.execute.return_value = {
        "items": [
            {
                "id": "abcdefghijk",
                "snippet": {
                    "title": "Video",
                    "channelTitle": "Channel",
                    "description": "x" * 400,
                },
                "contentDetails": {"duration": "PT2M"},
                "statistics": {"viewCount": "10"},
            }
        ]
    }
    invoke(
        youtube,
        monkeypatch,
        ["info", "https://youtube.com/watch?v=abcdefghijk", "raw-id"],
    )
    videos.list.assert_called_once_with(
        part="snippet,contentDetails,statistics", id="abcdefghijk,raw-id"
    )
    result = json.loads(capsys.readouterr().out)[0]
    assert (
        result["duration"] == "PT2M"
        and len(result["description"]) == 300
        and result["like_count"] is None
    )
    search = Mock()
    monkeypatch.setattr(youtube.cli.youtube_videos, "search_videos", search)
    invoke(youtube, monkeypatch, ["search", "nix", "-n", "3"])
    search.assert_called_once_with("nix", 3)
