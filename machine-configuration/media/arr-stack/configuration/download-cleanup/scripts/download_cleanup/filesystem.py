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

    def linked_inode(self, path):
        if path.is_symlink():
            return set()
        stat = path.stat()
        return {(stat.st_dev, stat.st_ino)} if stat.st_nlink > 1 else set()

    def files(self, path):
        visited = 0
        for directory, _, filenames in os.walk(path):
            for filename in filenames:
                visited += 1
                if visited > 50000:
                    raise RuntimeError("media folder exceeds bootstrap file bound")
                yield Path(directory) / filename

    def linked_inodes(self, container_path):
        path = self.host_path(container_path)
        if not path.exists():
            return set()
        if path.is_file():
            return self.linked_inode(path)
        result = set()
        for item in self.files(path):
            result.update(self.linked_inode(item))
        return result
