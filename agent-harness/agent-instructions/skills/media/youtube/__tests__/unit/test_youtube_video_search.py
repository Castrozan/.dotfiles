import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def youtube_videos(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2] / "scripts"))
    return importlib.import_module("youtube_videos")


@pytest.mark.parametrize("query", ["music", "--exec=touch /tmp/unwanted", "'$(id);&"])
def test_search_query_remains_one_positional_argument(
    youtube_videos, monkeypatch, capsys, query
):
    recorded_arguments = []

    def run(arguments, **options):
        recorded_arguments.append(arguments)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(youtube_videos.subprocess, "run", run)
    youtube_videos.search_videos(query, max_results=3)

    assert recorded_arguments == [
        [
            "yt-dlp",
            "--dump-json",
            "--flat-playlist",
            "--no-warnings",
            "--",
            f"ytsearch3:{query}",
        ]
    ]
    assert json.loads(capsys.readouterr().out) == []


def test_search_preserves_video_metadata_and_blank_lines(
    youtube_videos, monkeypatch, capsys
):
    video = {"id": "example", "uploader": "channel", "description": "x" * 205}
    monkeypatch.setattr(
        youtube_videos.subprocess,
        "run",
        lambda *arguments, **options: SimpleNamespace(
            returncode=0, stdout="\n" + json.dumps(video) + "\n\n", stderr=""
        ),
    )

    youtube_videos.search_videos("example")

    assert json.loads(capsys.readouterr().out) == [
        {
            "id": "example",
            "title": None,
            "url": "https://www.youtube.com/watch?v=example",
            "channel": "channel",
            "duration": None,
            "view_count": None,
            "description": "x" * 200,
        }
    ]


def test_failed_search_reports_the_downloader_error(
    youtube_videos, monkeypatch, capsys
):
    monkeypatch.setattr(
        youtube_videos.subprocess,
        "run",
        lambda *arguments, **options: SimpleNamespace(
            returncode=2, stdout="", stderr="download unavailable"
        ),
    )

    with pytest.raises(SystemExit) as error:
        youtube_videos.search_videos("example")

    assert error.value.code == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert json.loads(output.err) == {
        "error": "search_failed",
        "stderr": "download unavailable",
    }
