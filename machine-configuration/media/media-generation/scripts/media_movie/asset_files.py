import hashlib
import os
import stat

from media_movie.contract import MovieAsset, MovieError
from media_video.files import sync_file


def retain_movie_asset(directory, filename, asset):
    descriptor = os.open(asset.path, os.O_RDONLY | os.O_NOFOLLOW)
    destination = directory / filename
    digest = hashlib.sha256()
    copied = 0
    with os.fdopen(descriptor, "rb") as source:
        validate_scene_asset_metadata(os.fstat(source.fileno()))
        target_descriptor = os.open(
            destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
        )
        with os.fdopen(target_descriptor, "wb") as target:
            while chunk := source.read(1024 * 1024):
                copied += len(chunk)
                if copied > 64 * 1024 * 1024:
                    raise MovieError("scene_asset_size_limit_exceeded")
                digest.update(chunk)
                target.write(chunk)
            target.flush()
            os.fsync(target.fileno())
    if digest.hexdigest() != asset.sha256:
        raise MovieError("scene_asset_checksum_mismatch")
    return MovieAsset(destination, asset.sha256, asset.duration_seconds)


def validate_scene_asset_metadata(metadata):
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or not 0 < metadata.st_size <= 64 * 1024 * 1024
    ):
        raise MovieError("invalid_scene_asset")


def asset_checksum(path):
    if (
        path.is_symlink()
        or not path.is_file()
        or path.stat().st_size > 2 * 1024 * 1024 * 1024
    ):
        raise MovieError("invalid_movie_asset")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def describe_movie_outputs(directory):
    assets = {}
    for name, filename, mime_type in (
        ("video", "render.mp4", "video/mp4"),
        ("thumbnail", "thumbnail.png", "image/png"),
    ):
        path = directory / filename
        path.chmod(0o600)
        sync_file(path)
        assets[name] = {
            "path": str(path),
            "mime_type": mime_type,
            "sha256": asset_checksum(path),
            "size_bytes": path.stat().st_size,
        }
    return assets
