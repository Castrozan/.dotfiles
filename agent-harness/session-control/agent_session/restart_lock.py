import fcntl
import os
import secrets
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

RESTART_WAIT_SECONDS = 30
RESTART_LOCK_STALE_SECONDS = RESTART_WAIT_SECONDS * 2 + 15


@dataclass(frozen=True)
class RestartLock:
    path: Path
    owner_token: str


def restart_lock_path_for(process_identifier: int) -> Path:
    return Path("/tmp") / f"agent-session-restart-{process_identifier}.lock"


def restart_lock_is_stale(lock_path: Path) -> bool:
    try:
        return time.time() - lock_path.stat().st_mtime > RESTART_LOCK_STALE_SECONDS
    except FileNotFoundError:
        return False


def restart_lock_owner_token_at(lock_path: Path) -> str | None:
    try:
        return lock_path.read_text()
    except FileNotFoundError:
        return None


@contextmanager
def restart_lock_guard(lock_path: Path) -> Iterator[None]:
    guard_path = lock_path.with_name(f"{lock_path.name}.guard")
    guard_file_descriptor = os.open(guard_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(guard_file_descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(guard_file_descriptor, fcntl.LOCK_UN)
        os.close(guard_file_descriptor)


def create_restart_lock(lock_path: Path) -> RestartLock:
    owner_token = secrets.token_hex(16)
    lock_file_descriptor = os.open(
        lock_path,
        os.O_CREAT | os.O_EXCL | os.O_WRONLY,
        0o600,
    )
    try:
        os.write(lock_file_descriptor, owner_token.encode())
    finally:
        os.close(lock_file_descriptor)
    return RestartLock(lock_path, owner_token)


def release_restart_lock_if_owned(restart_lock: RestartLock) -> None:
    if restart_lock_owner_token_at(restart_lock.path) != restart_lock.owner_token:
        return
    try:
        restart_lock.path.unlink()
    except FileNotFoundError:
        return


def acquire_restart_lock(process_identifier: int) -> RestartLock | None:
    lock_path = restart_lock_path_for(process_identifier)
    with restart_lock_guard(lock_path):
        try:
            return create_restart_lock(lock_path)
        except FileExistsError:
            existing_owner_token = restart_lock_owner_token_at(lock_path)
            if not restart_lock_is_stale(lock_path) or existing_owner_token is None:
                return None
            release_restart_lock_if_owned(RestartLock(lock_path, existing_owner_token))
            return create_restart_lock(lock_path)


def restart_lock_is_owned(restart_lock: RestartLock) -> bool:
    with restart_lock_guard(restart_lock.path):
        return (
            restart_lock_owner_token_at(restart_lock.path) == restart_lock.owner_token
        )


def execute_while_restart_lock_is_owned(
    restart_lock: RestartLock, action: Callable[[], None]
) -> bool:
    with restart_lock_guard(restart_lock.path):
        if restart_lock_owner_token_at(restart_lock.path) != restart_lock.owner_token:
            return False
        action()
        return True


def release_restart_lock(restart_lock: RestartLock) -> None:
    with restart_lock_guard(restart_lock.path):
        release_restart_lock_if_owned(restart_lock)
