import time

import listener
import transcript_log

POLL_SECONDS = 0.1
SETTLE_SECONDS = 0.5
UNFINISHED_SPEECH_LIMIT_SECONDS = 120


class ConversationClosed(Exception):
    pass


def forget(directory):
    (directory / "heard").unlink(missing_ok=True)


def last_heard(directory):
    path = directory / "heard"
    return int(path.read_text()) if path.exists() else 0


def remember(directory, sequence):
    (directory / "heard").write_text(str(sequence))


def wait_for_first_entries(directory, wait_seconds, still_open):
    transcript = directory / "transcript.jsonl"
    deadline = time.monotonic() + wait_seconds
    while True:
        if not still_open():
            raise ConversationClosed("No conversation is open; run avatar-talk open")
        slice_seconds = min(max(deadline - time.monotonic(), 0), 1)
        entries = transcript_log.wait_since(
            transcript, last_heard(directory), slice_seconds
        )
        if entries or time.monotonic() >= deadline:
            return entries


def wait_for_finished_speech(directory, entries):
    transcript = directory / "transcript.jsonl"
    in_progress = directory / listener.SPEECH_IN_PROGRESS_MARKER
    settled_at = time.monotonic() + SETTLE_SECONDS
    limit = time.monotonic() + UNFINISHED_SPEECH_LIMIT_SECONDS
    while time.monotonic() < limit:
        latest = transcript_log.read_since(transcript, last_heard(directory))
        if len(latest) > len(entries):
            entries = latest
            settled_at = time.monotonic() + SETTLE_SECONDS
        if time.monotonic() >= settled_at and not in_progress.exists():
            break
        time.sleep(POLL_SECONDS)
    return entries


def next_utterance(directory, wait_seconds, still_open):
    entries = wait_for_first_entries(directory, wait_seconds, still_open)
    if not entries:
        return None
    entries = wait_for_finished_speech(directory, entries)
    remember(directory, entries[-1]["sequence"])
    return " ".join(entry["text"] for entry in entries)
