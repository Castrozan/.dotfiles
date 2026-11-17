import fcntl
import json
import sys
import time
import urllib.parse

import listener_runtime

CLAIM_SECONDS = 10
CLAIMS_DIRECTORY = "wake-claims"
USAGE_ERROR = 2


def claim_path(directory, pane):
    return directory / CLAIMS_DIRECTORY / f"pane-{urllib.parse.quote(pane, safe='')}"


def recorded_claim(text):
    try:
        record = json.loads(text)
    except ValueError:
        return None, 0.0
    return record.get("room"), float(record.get("claimed_at", 0.0))


def held_by_another_room(text, room, now):
    holder, claimed_at = recorded_claim(text)
    return bool(holder) and holder != room and now - claimed_at < CLAIM_SECONDS


def claim(directory, pane, room, now):
    path = claim_path(directory, pane)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        handle.seek(0)
        if held_by_another_room(handle.read(), room, now):
            return False
        handle.truncate(0)
        handle.write(json.dumps({"room": room, "claimed_at": now}))
        handle.flush()
        return True


def exit_status(pane, room):
    if not room:
        print("--claim needs --room", file=sys.stderr)
        return USAGE_ERROR
    won = claim(listener_runtime.runtime_directory(), pane, room, time.time())
    return 0 if won else 1
