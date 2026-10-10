import os
from unittest.mock import Mock

import pytest

from download_cleanup.bootstrap import bootstrap
from download_cleanup.domain import Media, scoped_path, validate_download_paths
from download_cleanup.filesystem import Filesystem
from download_cleanup.ledger import Ledger


def test_bootstrap_uses_history_hashes_and_hardlinks_for_existing_media(tmp_path):
    data = tmp_path / "data"
    library = data / "media/tv/Example"
    library.mkdir(parents=True)
    downloads = data / "torrents"
    downloads.mkdir()
    (downloads / "Example.mkv").write_bytes(b"media")
    os.link(downloads / "Example.mkv", library / "Episode.mkv")
    media = Media("sonarr", 12, 1234, "Example", "/data/media/tv/Example")
    media_client = Mock()
    media_client.media.return_value = [
        {"id": 12, "tvdbId": 1234, "title": "Example", "path": media.library_path}
    ]
    media_client.history.return_value = [
        {"seriesId": 12, "downloadId": "A" * 40},
        {"seriesId": 99, "downloadId": "b" * 40},
        {"seriesId": 12, "downloadId": "invalid"},
    ]
    torrents = Mock()
    torrents.list.return_value = [
        {"hash": "a" * 40, "content_path": "/data/torrents/History.mkv"},
        {"hash": "c" * 40, "content_path": "/data/torrents/Example.mkv"},
        {"hash": "d" * 40, "content_path": "/data/audiobooks/Other"},
    ]
    filesystem = Filesystem(data)
    filesystem.assert_mounted = Mock()
    ledger = Ledger(tmp_path / "cleanup.sqlite")
    bootstrap(ledger, {"sonarr": media_client}, torrents, filesystem)
    assert ledger.downloads(media) == [("a" * 40, ""), ("c" * 40, "")]
    assert ledger.pending() == []
    torrents.delete.assert_not_called()


@pytest.mark.parametrize(
    "path",
    ["/data/torrents", "/data/torrents/../media/Film", "/etc/passwd", "relative.mkv"],
)
def test_out_of_scope_download_paths_are_rejected(path):
    with pytest.raises(ValueError):
        validate_download_paths([path], [])


def test_library_root_cannot_be_a_media_target():
    with pytest.raises(ValueError):
        scoped_path("/data/media/tv", "/data/media", 5)


def test_symlink_cannot_redirect_cleanup_outside_download_storage(tmp_path):
    (tmp_path / "torrents").mkdir()
    outside = tmp_path / "media"
    outside.mkdir()
    (tmp_path / "torrents/redirect").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="outside"):
        Filesystem(tmp_path).validate_download("/data/torrents/redirect/film.mkv")


def test_unmounted_drive_blocks_cleanup(tmp_path):
    with pytest.raises(RuntimeError, match="not mounted"):
        Filesystem(tmp_path).assert_mounted()
