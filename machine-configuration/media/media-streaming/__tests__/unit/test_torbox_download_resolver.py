import importlib
import sys
import urllib.parse
from pathlib import Path

import pytest


PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "stremio_gateway"
)
sys.path.insert(0, str(PACKAGE_DIRECTORY_PATH))
torbox_download_resolver = importlib.import_module("torbox_download_resolver")


def test_uses_the_actual_episode_file_id_and_reuses_links_for_range_requests(
    monkeypatch,
):
    requested = []
    filename = "Attack on Titan - S01E01.mkv"
    period = [0]
    monkeypatch.setattr(torbox_download_resolver.time, "monotonic", lambda: period[0])

    def request(request):
        requested.append(request)
        if "/mylist?" in request.full_url:
            return {
                "data": [
                    {
                        "id": 123,
                        "hash": "a" * 40,
                        "files": [
                            {"id": 0, "name": "Season 4/S04E29.mkv"},
                            {"id": 43, "name": f"Season 1/{filename}"},
                        ],
                    }
                ]
            }
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(request.full_url).query)
        assert query["torrent_id"] == ["123"]
        assert query["file_id"] == ["43"]
        return {"data": "https://media.example/correct-episode?token=secret"}

    resolver = torbox_download_resolver.TorBoxDownloadResolver("secret", request)
    target = f"/configuration/playback/{'a' * 40}/0/0/1/1?" + urllib.parse.urlencode(
        {"torrent_name": filename}
    )
    expected_url = "https://media.example/correct-episode?token=secret"
    assert resolver.download_url(target) == expected_url
    assert resolver.download_url(target) == expected_url
    assert len(requested) == 2
    period[0] = torbox_download_resolver.DOWNLOAD_LINK_CACHE_SECONDS + 1
    assert resolver.download_url(target) == expected_url
    assert len(requested) == 4


@pytest.mark.parametrize(
    "files",
    [
        [],
        [
            {"id": 1, "name": "A/S01E01.mkv"},
            {"id": 2, "name": "B/S01E01.mkv"},
        ],
    ],
)
def test_does_not_fall_back_to_an_unrelated_or_ambiguous_episode(files):
    resolver = torbox_download_resolver.TorBoxDownloadResolver(
        "secret",
        lambda request: {"data": [{"id": 1, "hash": "a" * 40, "files": files}]},
    )
    target = f"/playback/{'a' * 40}/0/0/1/1?torrent_name=S01E01.mkv"
    with pytest.raises(RuntimeError, match="unavailable or ambiguous"):
        resolver.download_url(target)
