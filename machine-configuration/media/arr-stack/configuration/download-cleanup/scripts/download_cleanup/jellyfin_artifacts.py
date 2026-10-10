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

    def cache_prefixes(self, root):
        if not root.exists():
            return
        for prefix in root.iterdir():
            if self.cache_prefix(prefix):
                yield prefix

    def cache_candidates(self):
        for root in self.cache_directories:
            for prefix in self.cache_prefixes(root):
                yield from ((root, directory) for directory in prefix.iterdir())

    def cache_prefix(self, path):
        return all((not path.is_symlink(), path.is_dir(), len(path.name) == 2))

    def cache_identifier(self, path):
        if any((path.is_symlink(), not path.is_dir())):
            return None
        try:
            identifier = UUID(path.name).hex
        except ValueError:
            return None
        if identifier[:2] != path.parent.name.lower():
            return None
        return identifier

    def retained_cache(self, path, retained):
        identifier = self.cache_identifier(path)
        return any((identifier is None, identifier in retained))

    def remove_cache(self, root, directory):
        if not directory.resolve().is_relative_to(root.resolve()):
            raise ValueError("Jellyfin cache path escapes its root")
        shutil.rmtree(directory)

    def clean(self):
        retained = {UUID(identifier).hex for identifier, _ in self.catalogue()}
        removed = 0
        for visited, (root, directory) in enumerate(self.cache_candidates(), start=1):
            if visited > 200000:
                raise RuntimeError("Jellyfin cache exceeds cleanup bound")
            if self.retained_cache(directory, retained):
                continue
            self.remove_cache(root, directory)
            removed += 1
        return removed
