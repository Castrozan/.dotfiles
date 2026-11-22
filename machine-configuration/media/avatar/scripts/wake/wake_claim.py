import fcntl
import json
import os
import subprocess
import sys
import time
import urllib.parse

import conversation_addressee
import listener_runtime
import remote_agent

CLAIM_SECONDS = 10
CLAIMS_DIRECTORY = "wake-claims"
USAGE_ERROR = 2
ROOM_QUERY_SECONDS = 5


def active_conversation(directory):
    addressee = conversation_addressee.current(directory)
    if addressee is None or not listener_runtime.listening():
        return None
    return {
        "host": addressee.host or os.environ[remote_agent.HOST_ENVIRONMENT_VARIABLE],
        "pane": addressee.pane,
    }


def conversation_report():
    return json.dumps(active_conversation(listener_runtime.runtime_directory()))


def conversation_in_room(directory, room):
    if room == os.environ[remote_agent.HOST_ENVIRONMENT_VARIABLE]:
        return active_conversation(directory)
    answer = subprocess.run(
        remote_agent.on_host(room, ["avatar-wake", "--conversation"]),
        capture_output=True,
        text=True,
        check=True,
        timeout=ROOM_QUERY_SECONDS,
    )
    try:
        conversation = json.loads(answer.stdout)
        if conversation is not None and (
            not isinstance(conversation, dict)
            or set(conversation) != {"host", "pane"}
            or not all(isinstance(value, str) for value in conversation.values())
        ):
            raise ValueError("invalid conversation identity")
        return conversation
    except (KeyError, TypeError, ValueError) as error:
        raise ConnectionError(f"Cannot verify the conversation on {room}") from error


def matches_session(conversation, pane):
    return conversation == {
        "host": os.environ[remote_agent.HOST_ENVIRONMENT_VARIABLE],
        "pane": pane,
    }


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
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        handle.seek(0)
        recorded = handle.read()
        if room != os.environ[
            remote_agent.HOST_ENVIRONMENT_VARIABLE
        ] and matches_session(active_conversation(directory), pane):
            return False
        if held_by_another_room(recorded, room, now):
            return False
        previous_room, _ = recorded_claim(recorded)
        if (
            previous_room
            and previous_room != room
            and matches_session(conversation_in_room(directory, previous_room), pane)
        ):
            return False
        handle.truncate(0)
        handle.write(json.dumps({"room": room, "claimed_at": now}))
        handle.flush()
        return True


def exit_status(pane, room):
    if not room:
        print("--claim needs --room", file=sys.stderr)
        return USAGE_ERROR
    try:
        won = claim(listener_runtime.runtime_directory(), pane, room, time.time())
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        print(f"Wake claim refused: {error}", file=sys.stderr)
        return USAGE_ERROR
    return 0 if won else 1
