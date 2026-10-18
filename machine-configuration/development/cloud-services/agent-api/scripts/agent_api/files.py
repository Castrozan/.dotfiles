import hashlib
import os
import stat
from pathlib import Path

from agent_api.contract import MAXIMUM_ARTIFACT_BYTES, CapabilityError, canonical_json


def private_directory(path):
    path = Path(path).expanduser().absolute()
    if path.resolve() != path:
        raise CapabilityError("unsafe_state_directory")
    path.mkdir(parents=True, mode=0o700, exist_ok=True)
    metadata = path.stat()
    if metadata.st_uid != os.geteuid() or stat.S_IMODE(metadata.st_mode) & 0o077:
        raise CapabilityError("private_directory_required")
    return path


def input_file(value):
    path = Path(value).expanduser()
    try:
        metadata = path.lstat()
    except OSError:
        raise CapabilityError("input_unavailable") from None
    if (
        not path.is_absolute()
        or not stat.S_ISREG(metadata.st_mode)
        or path.resolve() != path
        or metadata.st_uid != os.geteuid()
        or metadata.st_size > MAXIMUM_ARTIFACT_BYTES
    ):
        raise CapabilityError("invalid_input_file")
    return path


def file_digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    temporary = path.with_suffix(".pending")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical_json(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def describe_artifacts(directory):
    artifacts = []
    total_bytes = 0
    for path in sorted(directory.glob("*")):
        if path.name in (
            "request.json",
            "result.json",
            "worker.log",
            "submission.json",
        ):
            continue
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode):
            raise CapabilityError("invalid_artifact")
        total_bytes += metadata.st_size
        if total_bytes > MAXIMUM_ARTIFACT_BYTES:
            raise CapabilityError("artifact_too_large")
        artifacts.append(
            {
                "path": path.name,
                "size_bytes": metadata.st_size,
                "sha256": file_digest(path),
            }
        )
    return artifacts


def verify_artifacts(directory, artifacts):
    for artifact in artifacts:
        path = directory / artifact["path"]
        if (
            path.parent != directory
            or path.is_symlink()
            or not path.is_file()
            or path.stat().st_size != artifact["size_bytes"]
            or file_digest(path) != artifact["sha256"]
        ):
            raise CapabilityError("artifact_changed")
