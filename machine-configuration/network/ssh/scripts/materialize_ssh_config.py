import os
import stat
import sys
import tempfile
from pathlib import Path


def destination_identity(destination):
    try:
        metadata = destination.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.geteuid():
        raise ValueError("SSH config destination must be a user-owned regular file")
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def materialize_ssh_config(source, destination):
    directory = destination.parent
    metadata = directory.lstat()
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.geteuid()
        or metadata.st_mode & 0o022
    ):
        raise ValueError(
            "SSH config directory must be user-owned and not writable by other users"
        )
    original_identity = destination_identity(destination)
    content = source.read_bytes()
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=directory, prefix=".config-", delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            os.fchmod(temporary.fileno(), 0o600)
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        if destination_identity(destination) != original_identity:
            raise RuntimeError(
                "SSH config changed during activation; preserving the concurrent edit"
            )
        os.replace(temporary_path, destination)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


if __name__ == "__main__":
    materialize_ssh_config(Path(sys.argv[1]), Path(sys.argv[2]))
