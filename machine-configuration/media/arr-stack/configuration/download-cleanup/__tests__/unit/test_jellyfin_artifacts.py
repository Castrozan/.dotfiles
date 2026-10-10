import sqlite3
from uuid import UUID

import pytest

from download_cleanup.domain import Media
from download_cleanup.jellyfin_artifacts import JellyfinArtifacts


def artifacts_for(tmp_path, records):
    artifacts = JellyfinArtifacts(tmp_path)
    artifacts.database_path.parent.mkdir(parents=True)
    with sqlite3.connect(artifacts.database_path) as connection:
        connection.execute("CREATE TABLE BaseItems(Id TEXT,Path TEXT)")
        connection.executemany("INSERT INTO BaseItems VALUES (?,?)", records)
    return artifacts


def cache_directory(root, identifier):
    directory = root / UUID(identifier).hex[:2] / identifier
    directory.mkdir(parents=True)
    (directory / "data").write_bytes(b"cache")
    return directory


def test_only_orphaned_subtitle_and_metadata_directories_are_removed(tmp_path):
    retained = "a" * 32
    removed = "b" * 32
    artifacts = artifacts_for(tmp_path, [(retained, "/media/tv/Retained/episode.mkv")])
    existing = []
    deleted = []
    for root in artifacts.cache_directories:
        existing.append(cache_directory(root, str(UUID(retained))))
        deleted.append(cache_directory(root, str(UUID(removed))))
        unknown = root / "aa/not-a-source-id"
        unknown.mkdir(parents=True)
        existing.append(unknown)
    assert artifacts.clean() == 2
    assert all(path.exists() for path in existing)
    assert all(not path.exists() for path in deleted)


def test_catalogue_paths_are_checked_without_matching_sibling_titles(tmp_path):
    artifacts = artifacts_for(
        tmp_path, [("a" * 32, "/media/tv/Example Two/Episode.mkv")]
    )
    media = Media("sonarr", 12, 1234, "Example", "/data/media/tv/Example")
    assert not artifacts.contains(media)
    with sqlite3.connect(artifacts.database_path) as connection:
        connection.execute(
            "INSERT INTO BaseItems VALUES (?,?)",
            ("b" * 32, "/media/tv/Example/Season 1/Episode.mkv"),
        )
    assert artifacts.contains(media)


def test_empty_catalogue_cannot_authorize_cache_deletion(tmp_path):
    artifacts = artifacts_for(tmp_path, [])
    directory = cache_directory(artifacts.cache_directories[0], "a" * 32)
    with pytest.raises(RuntimeError, match="empty"):
        artifacts.clean()
    assert directory.exists()


def test_symlinked_cache_directories_are_preserved(tmp_path):
    artifacts = artifacts_for(tmp_path, [("a" * 32, "/media/tv/Retained/Episode.mkv")])
    outside = tmp_path / "outside"
    outside.mkdir()
    prefix = artifacts.cache_directories[0] / "bb"
    prefix.mkdir(parents=True)
    (prefix / ("b" * 32)).symlink_to(outside, target_is_directory=True)
    assert artifacts.clean() == 0
    assert outside.exists()
