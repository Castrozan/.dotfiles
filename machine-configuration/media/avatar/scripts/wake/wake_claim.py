import fcntl
import os
import sys
import time
import urllib.parse

import listener_runtime

CLAIM_SECONDS = 10
CLAIMS_DIRECTORY = "wake-claims"
USAGE_ERROR = 2


def claim_path(directory, pane):
    return directory / CLAIMS_DIRECTORY / f"pane-{urllib.parse.quote(pane, safe='')}"


def held_by_another_room(holder, room, claimed_at, now):
    return bool(holder) and holder != room and now - claimed_at < CLAIM_SECONDS


def claim(directory, pane, room, now):
    path = claim_path(directory, pane)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        handle.seek(0)
        holder = handle.read()
        if held_by_another_room(holder, room, os.fstat(handle.fileno()).st_mtime, now):
            return False
        handle.truncate(0)
        handle.write(room)
        handle.flush()
        os.utime(handle.fileno(), (now, now))
        return True


def exit_status(pane, room):
    if not room:
        print("--claim needs --room", file=sys.stderr)
        return USAGE_ERROR
    won = claim(listener_runtime.runtime_directory(), pane, room, time.time())
    return 0 if won else 1
