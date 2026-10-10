import shutil
import sqlite3
from pathlib import Path, PurePosixPath
from uuid import UUID


class JellyfinArtifacts:
    def __init__(self, config_directory):
        config_directory = Path(config_directory)
        self.database_path = config_directory / "data/data/jellyfin.db"
        self.cache_directories = (
            config_directory / "data/data/subtitles",
            config_directory / "data/metadata/library",
        )

    def catalogue(self):
        with sqlite3.connect(
            f"file:{self.database_path}?mode=ro", uri=True
        ) as connection:
            records = connection.execute(
                "SELECT Id,Path FROM BaseItems LIMIT 200001"
            ).fetchall()
        if not records or len(records) > 200000:
            raise RuntimeError("Jellyfin catalogue exceeds cleanup bounds or is empty")
        return records

    def contains(self, media):
        library_path = PurePosixPath("/media") / PurePosixPath(
            media.library_path
        ).relative_to("/data/media")
        return any(
            path
            and (
                PurePosixPath(path) == library_path
                or library_path in PurePosixPath(path).parents
            )
            for _, path in self.catalogue()
        )

    def clean(self):
        retained = {UUID(identifier).hex for identifier, _ in self.catalogue()}
        removed = 0
        for cache_directory in self.cache_directories:
            if not cache_directory.exists():
                continue
            visited = 0
            for prefix in cache_directory.iterdir():
                if prefix.is_symlink() or not prefix.is_dir() or len(prefix.name) != 2:
                    continue
                for directory in prefix.iterdir():
                    visited += 1
                    if visited > 200000:
                        raise RuntimeError("Jellyfin cache exceeds cleanup bound")
                    if directory.is_symlink() or not directory.is_dir():
                        continue
                    try:
                        identifier = UUID(directory.name).hex
                    except ValueError:
                        continue
                    if identifier[:2] != prefix.name.lower() or identifier in retained:
                        continue
                    if not directory.resolve().is_relative_to(
                        cache_directory.resolve()
                    ):
                        raise ValueError("Jellyfin cache path escapes its root")
                    shutil.rmtree(directory)
                    removed += 1
        return removed
