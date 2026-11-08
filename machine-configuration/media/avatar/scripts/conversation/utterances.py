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
OPEN_CHECK_SECONDS = 1
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


class ThrottledCheck:
    def __init__(self, check, interval_seconds):
        self.check = check
        self.interval_seconds = interval_seconds
        self.next_check_at = time.monotonic()
        self.last_answer = True

    def passes(self):
        if time.monotonic() >= self.next_check_at:
            self.last_answer = self.check()
            self.next_check_at = time.monotonic() + self.interval_seconds
        return self.last_answer


class SpeechSettling:
    def __init__(self, directory, entries):
        self.directory = directory
        self.in_progress = directory / listener.SPEECH_IN_PROGRESS_MARKER
        self.entries = entries
        self.settled_at = time.monotonic() + settle_seconds_after(entries)

    def refresh(self):
        latest = transcript_log.read_since(
            self.directory / "transcript.jsonl", last_heard(self.directory)
        )
        if len(latest) > len(self.entries):
            self.entries = latest
            self.settled_at = time.monotonic() + settle_seconds_after(latest)

    def settled(self):
        return time.monotonic() >= self.settled_at and not self.in_progress.exists()


def wait_for_finished_speech(directory, entries, still_open):
    settling = SpeechSettling(directory, entries)
    conversation_still_open = ThrottledCheck(still_open, OPEN_CHECK_SECONDS)
    limit = time.monotonic() + UNFINISHED_SPEECH_LIMIT_SECONDS
    while time.monotonic() < limit and conversation_still_open.passes():
        settling.refresh()
        if settling.settled():
            break
        time.sleep(POLL_SECONDS)
    return settling.entries


def next_utterance(directory, wait_seconds, still_open):
    entries = wait_for_first_entries(directory, wait_seconds, still_open)
    if not entries:
        return None
    entries = wait_for_finished_speech(directory, entries, still_open)
    remember(directory, entries[-1]["sequence"])
    return " ".join(entry["text"] for entry in entries)
