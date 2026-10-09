import errno
import fcntl
import os
import stat
import sys


def validate_lock_file(lock_path, file_descriptor):
    opened_file = os.fstat(file_descriptor)
    named_file = os.lstat(lock_path)
    if not stat.S_ISREG(opened_file.st_mode) or opened_file.st_nlink != 1:
        raise OSError("exclusive run lock must be a regular file with one link")
    if (opened_file.st_dev, opened_file.st_ino) != (
        named_file.st_dev,
        named_file.st_ino,
    ):
        raise OSError("exclusive run lock path changed during acquisition")


def prepare_lock_file(lock_path):
    try:
        file_descriptor = os.open(
            lock_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
        )
    except FileNotFoundError:
        try:
            file_descriptor = os.open(
                lock_path, os.O_RDONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o666
            )
        except FileExistsError:
            return prepare_lock_file(lock_path)
        os.fchmod(file_descriptor, 0o666)
    try:
        validate_lock_file(lock_path, file_descriptor)
    finally:
        os.close(file_descriptor)


def acquire_lock_file(lock_path, file_descriptor):
    validate_lock_file(lock_path, file_descriptor)
    try:
        fcntl.flock(file_descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as error:
        if error.errno in (errno.EACCES, errno.EAGAIN):
            return 99
        raise
    validate_lock_file(lock_path, file_descriptor)
    return 0


def write_lock_metadata(lock_path, file_descriptor):
    validate_lock_file(lock_path, file_descriptor)
    with os.fdopen(os.open(lock_path, os.O_WRONLY | os.O_NOFOLLOW), "wb") as metadata:
        validate_lock_file(lock_path, metadata.fileno())
        metadata.truncate(0)
        metadata.write(sys.stdin.buffer.read(8192))


def main():
    action, lock_path = sys.argv[1:3]
    try:
        if action == "prepare":
            prepare_lock_file(lock_path)
            return 0
        file_descriptor = int(sys.argv[3])
        if action == "acquire":
            return acquire_lock_file(lock_path, file_descriptor)
        if action == "write":
            write_lock_metadata(lock_path, file_descriptor)
            return 0
        raise ValueError("unknown exclusive run lock action")
    except (OSError, ValueError) as error:
        print(f"error: exclusive run lock unavailable: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
