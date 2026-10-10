import os
from pathlib import Path

from .domain import scoped_path


class Filesystem:
    def __init__(self, data_directory):
        self.data_directory = Path(data_directory)

    def assert_mounted(self):
        if not os.path.ismount(self.data_directory):
            raise RuntimeError("media data drive is not mounted")

    def host_path(self, container_path):
        return self.data_directory / Path(container_path).relative_to("/data")

    def library_exists(self, path):
        scoped_path(path, "/data/media", 5)
        return self.host_path(path).exists()

    def validate_download(self, path):
        scoped_path(path, "/data/torrents", 4)
        host_path = self.host_path(path)
        if not host_path.resolve().is_relative_to(
            (self.data_directory / "torrents").resolve()
        ):
            raise ValueError("download path resolves outside torrent storage")

    def download_exists(self, path):
        self.validate_download(path)
        return self.host_path(path).exists()

    def linked_inodes(self, container_path):
        path = self.host_path(container_path)
        if not path.exists():
            return set()
        if path.is_file():
            stat = path.stat()
            return {(stat.st_dev, stat.st_ino)} if stat.st_nlink > 1 else set()
        result = set()
        visited = 0
        for directory, _, filenames in os.walk(path):
            for filename in filenames:
                visited += 1
                if visited > 50000:
                    raise RuntimeError("media folder exceeds bootstrap file bound")
                item = Path(directory) / filename
                if item.is_symlink():
                    continue
                stat = item.stat()
                if stat.st_nlink > 1:
                    result.add((stat.st_dev, stat.st_ino))
        return result
