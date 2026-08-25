import importlib
import sys
import urllib.parse
from pathlib import Path

import pytest


PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "stremio_gateway"
)
sys.path.insert(0, str(PACKAGE_DIRECTORY_PATH))

stremio_gateway = importlib.import_module("stremio_gateway")


def torrent_result(title, category, seeders, size, info_hash):
    return {
        "title": title,
        "protocol": "torrent",
        "categories": [{"id": category}],
        "seeders": seeders,
        "size": size,
        "infoHash": info_hash,
    }


def request_fixture(metadata, results, requests):
    def request(url, headers=None):
        requests.append((url, headers))
        return {"meta": metadata} if "/meta/" in url else results

    return request


def test_parses_only_supported_stremio_stream_paths():
    assert stremio_gateway.parse_stream_request(
        "/prowlarr/stream/movie/tt1392170.json"
    ) == stremio_gateway.StreamRequest("movie", "tt1392170")
    assert stremio_gateway.parse_stream_request(
        "/prowlarr/stream/series/tt0944947:2:3.json"
    ) == stremio_gateway.StreamRequest("series", "tt0944947", 2, 3)
    assert (
        stremio_gateway.parse_stream_request(
            "/prowlarr/stream/movie/tt1392170:1:1.json"
        )
        is None
    )


def test_movie_search_uses_metadata_and_returns_ranked_single_movie_torrents():
    requests = []
    results = [
        torrent_result("The Hunger Games 2012 1080p", 2040, 10, 8_000, "A" * 40),
        torrent_result(
            "The Hunger Games Collection 2012-2023", 2040, 50, 50_000, "B" * 40
        ),
        torrent_result("The Hunger Games 2012 1080p", 5040, 100, 2_000, "C" * 40),
        torrent_result("The Hunger Games 2012 1080p", 2040, 20, 2_000, "D" * 40),
        torrent_result("The Hunger Games 2012 1080p", 2040, 30, 2_000, "invalid"),
    ]
    provider = stremio_gateway.ProwlarrStreamProvider(
        "http://100.64.0.1:9696",
        "runtime-secret",
        "https://v3-cinemeta.strem.io",
        request_fixture(
            {"name": "The Hunger Games", "year": "2012"}, results, requests
        ),
    )

    streams = provider.streams(stremio_gateway.StreamRequest("movie", "tt1392170"))

    assert [stream["infoHash"] for stream in streams] == ["D" * 40, "A" * 40]
    assert requests[0][0].endswith("/meta/movie/tt1392170.json")
    assert urllib.parse.parse_qs(urllib.parse.urlsplit(requests[1][0]).query) == {
        "query": ["The Hunger Games 2012 1080p"]
    }
    assert requests[1][1]["X-Api-Key"] == "runtime-secret"


def test_series_search_returns_only_the_requested_episode():
    requests = []
    results = [
        torrent_result("Game of Thrones S02E03 1080p", 5040, 20, 4_000, "A" * 40),
        torrent_result("Game of Thrones S02E04 1080p", 5040, 40, 4_000, "B" * 40),
        torrent_result("Game of Thrones S02E03 1080p", 2040, 60, 4_000, "C" * 40),
    ]
    provider = stremio_gateway.ProwlarrStreamProvider(
        "http://100.64.0.1:9696",
        "runtime-secret",
        "https://v3-cinemeta.strem.io",
        request_fixture({"name": "Game of Thrones"}, results, requests),
    )

    streams = provider.streams(
        stremio_gateway.StreamRequest("series", "tt0944947", 2, 3)
    )

    assert [stream["infoHash"] for stream in streams] == ["A" * 40]
    assert "Game+of+Thrones+S02E03+1080p" in requests[1][0]


def test_setup_url_carries_the_server_and_addon_without_an_account():
    url = stremio_gateway.setup_url(
        "http://100.64.0.1:43212",
        "http://100.64.0.1:11470/",
        "http://100.64.0.1:43212/prowlarr/manifest.json",
    )

    assert url.startswith(
        "http://100.64.0.1:43212/#/addons?addon=http%3A%2F%2F100.64.0.1%3A43212%2Fprowlarr%2Fmanifest.json"
    )
    assert "&streamingServerUrl=http%3A%2F%2F100.64.0.1%3A11470%2F" in url


def test_missing_prowlarr_api_key_refuses_to_start(tmp_path):
    config_file = tmp_path / "config.xml"
    config_file.write_text("<Config></Config>", encoding="utf-8")

    with pytest.raises(RuntimeError, match="API key is missing"):
        stremio_gateway.read_prowlarr_api_key(config_file)
