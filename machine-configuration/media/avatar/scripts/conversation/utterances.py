import contextlib
import fcntl
import os
import time

import listener
import transcript_log

POLL_SECONDS = 0.1
SETTLE_SECONDS = 0.5
UNFINISHED_TURN_SETTLE_SECONDS = 2.5
UNFINISHED_SPEECH_LIMIT_SECONDS = 120
CLOSED_MESSAGE = "No conversation is open; run avatar-talk open"
CONSUMER_BUSY_MESSAGE = "Another avatar-talk hear, ask or follow is already listening"
CONSUMER_LOCK_FILE = "heard.lock"


class ConversationClosed(Exception):
    pass


class ConversationBusy(RuntimeError):
    pass


@contextlib.contextmanager
def exclusive_consumer(directory):
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(directory / CONSUMER_LOCK_FILE, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as error:
        os.close(descriptor)
        raise ConversationBusy(CONSUMER_BUSY_MESSAGE) from error
    try:
        yield
    finally:
        os.close(descriptor)


def last_heard(directory):
    path = directory / listener.HEARD_FILE
    return int(path.read_text()) if path.exists() else 0


def remember(directory, sequence):
    (directory / listener.HEARD_FILE).write_text(str(sequence))


def wait_for_first_entries(directory, wait_seconds, still_open):
    transcript = directory / "transcript.jsonl"
    deadline = time.monotonic() + wait_seconds
    while True:
        if not still_open():
            raise ConversationClosed(CLOSED_MESSAGE)
        slice_seconds = min(max(deadline - time.monotonic(), 0), 1)
        entries = transcript_log.wait_since(
            transcript, last_heard(directory), slice_seconds
        )
        if entries or time.monotonic() >= deadline:
            return entries


def settle_seconds_after(entries):
    if entries[-1].get("turn_finished", True):
        return SETTLE_SECONDS
    return UNFINISHED_TURN_SETTLE_SECONDS


def wait_for_finished_speech(directory, entries, still_open):
    transcript = directory / "transcript.jsonl"
    in_progress = directory / listener.SPEECH_IN_PROGRESS_MARKER
    settled_at = time.monotonic() + settle_seconds_after(entries)
    limit = time.monotonic() + UNFINISHED_SPEECH_LIMIT_SECONDS
    while time.monotonic() < limit and still_open():
        latest = transcript_log.read_since(transcript, last_heard(directory))
        if len(latest) > len(entries):
            entries = latest
            settled_at = time.monotonic() + settle_seconds_after(entries)
        if time.monotonic() >= settled_at and not in_progress.exists():
            break
        time.sleep(POLL_SECONDS)
    return entries


def next_utterance(directory, wait_seconds, still_open):
    entries = wait_for_first_entries(directory, wait_seconds, still_open)
    if not entries:
        return None
    entries = wait_for_finished_speech(directory, entries, still_open)
    remember(directory, entries[-1]["sequence"])
    return " ".join(entry["text"] for entry in entries)
