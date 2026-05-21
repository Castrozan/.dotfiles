"""Logging, session-id prefix, and single-instance lock for the compliance reviewer."""

import fcntl
import os
import sys
import time
from pathlib import Path

LOG_PREFIX = "end-of-work-compliance-review"

PERSISTENT_LOG_FILE_PATH = (
    Path.home() / ".claude" / "logs" / "end-of-work-compliance-review.log"
)

SINGLE_INSTANCE_LOCK_FILE_PATH = Path("/tmp") / "end-of-work-compliance-review.lock"

CURRENT_SESSION_ID_SHORT_PREFIX = ""


def get_session_id_short_prefix() -> str:
    return CURRENT_SESSION_ID_SHORT_PREFIX


def set_session_id_short_prefix(session_id_full: str) -> None:
    global CURRENT_SESSION_ID_SHORT_PREFIX
    CURRENT_SESSION_ID_SHORT_PREFIX = session_id_full[:8] if session_id_full else ""


def log_status(message: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    session_segment = (
        f"[{get_session_id_short_prefix()}] " if get_session_id_short_prefix() else ""
    )
    formatted_line = f"[{timestamp}] {session_segment}{LOG_PREFIX}: {message}"
    print(formatted_line, file=sys.stderr, flush=True)
    try:
        PERSISTENT_LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(PERSISTENT_LOG_FILE_PATH, "a") as log_file_handle:
            log_file_handle.write(formatted_line + "\n")
    except OSError:
        pass


def acquire_single_instance_lock_or_none():
    lock_file_handle = open(SINGLE_INSTANCE_LOCK_FILE_PATH, "w")
    try:
        fcntl.flock(lock_file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_file_handle.close()
        return None
    lock_file_handle.write(f"{os.getpid()}\n")
    lock_file_handle.flush()
    return lock_file_handle
