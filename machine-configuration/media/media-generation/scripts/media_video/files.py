import hashlib
import json
import os
import re
import stat

from media_video.contract import VideoError


def canonical_json(value):
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def valid_digest(value):
    return isinstance(value, str) and re.fullmatch("[a-f0-9]{64}", value) is not None


def regular_file(path):
    if "\x00" in str(path) or not path.is_absolute() or path.resolve() != path:
        raise VideoError("unsafe_input_path")
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.geteuid():
        raise VideoError("unsafe_input_path")
    return metadata


def private_directory(path):
    if "\x00" in str(path) or not path.is_absolute() or path.resolve() != path:
        raise VideoError("unsafe_state_directory")
    metadata = path.lstat()
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.geteuid()
        or metadata.st_mode & 0o077
    ):
        raise VideoError("private_directory_required")


def create_private_directory(path):
    if "\x00" in str(path) or not path.is_absolute() or path.resolve() != path:
        raise VideoError("unsafe_state_directory")
    missing = []
    ancestor = path
    while not ancestor.exists():
        missing.append(ancestor)
        ancestor = ancestor.parent
    for directory in reversed(missing):
        try:
            directory.mkdir(mode=0o700)
            sync_directory(directory.parent)
        except FileExistsError:
            pass
        private_directory(directory)
    private_directory(path)


def file_digest(path, deadline=None):
    metadata = regular_file(path)
    if metadata.st_size > 2 * 1024**3:
        raise VideoError("input_too_large")
    digest = hashlib.sha256()
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as input_file:
        while chunk := input_file.read(1024 * 1024):
            if deadline is not None:
                deadline.remaining()
            digest.update(chunk)
    return digest.hexdigest()


def unique_json_pairs(pairs):
    value = {}
    for key, entry in pairs:
        if key in value:
            raise VideoError("invalid_json")
        value[key] = entry
    return value


def read_json(path, private=False):
    metadata = regular_file(path)
    if metadata.st_size > 1024 * 1024:
        raise VideoError("input_too_large")
    if private:
        private_directory(path.parent)
        if metadata.st_mode & 0o077:
            raise VideoError("private_registration_required")
    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=unique_json_pairs)
    except ValueError:
        raise VideoError("invalid_json") from None
    if not isinstance(value, dict):
        raise VideoError("invalid_json")
    return value


def atomic_json(path, value):
    temporary = path.with_suffix(".pending")
    descriptor = os.open(
        temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(descriptor, "wb") as output:
        output.write(canonical_json(value) + b"\n")
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, path)
    sync_directory(path.parent)


def sync_directory(directory):
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def sync_file(path):
    regular_file(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def retained_file(path, directory, deadline=None):
    relative = path.relative_to(directory)
    return {
        "path": relative.as_posix(),
        "size_bytes": path.stat().st_size,
        "sha256": file_digest(path, deadline),
    }
