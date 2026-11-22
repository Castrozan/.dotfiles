import enum
import time

import listener
import transcript_log
import utterances

QUIET_WAIT_SECONDS = 3
REACTION_SECONDS = 1
STOPPED_REPLY_FILE = "stopped-reply"
STOPPED_STATUSES = ("interrupted", "cancelled")
WITHHELD = "withheld"


class WithheldReason(enum.StrEnum):
    QUEUED = "queued"
    SPEAKING = "speaking"
    UNHEARD = "unheard"


def queued_behind_a_stopped_reply(directory):
    record = directory / STOPPED_REPLY_FILE
    if not record.exists():
        return False
    return time.time() - record.stat().st_mtime < REACTION_SECONDS


def quiet_within(directory, seconds):
    in_progress = directory / listener.SPEECH_IN_PROGRESS_MARKER
    deadline = time.monotonic() + seconds
    while in_progress.exists():
        if time.monotonic() >= deadline:
            return False
        time.sleep(utterances.POLL_SECONDS)
    return True


def unheard_words(directory):
    return bool(
        transcript_log.read_since(
            directory / "transcript.jsonl", utterances.last_heard(directory)
        )
    )


def withheld_reason(directory):
    if queued_behind_a_stopped_reply(directory):
        return WithheldReason.QUEUED
    if not quiet_within(directory, QUIET_WAIT_SECONDS):
        return WithheldReason.SPEAKING
    if unheard_words(directory):
        return WithheldReason.UNHEARD
    return None


def remember_stopped_reply(directory):
    (directory / STOPPED_REPLY_FILE).touch(mode=0o600)


def remember_outcome(directory, status):
    if status in STOPPED_STATUSES:
        remember_stopped_reply(directory)


def withhold(directory, reason):
    remember_stopped_reply(directory)
    return {"type": "speakAck", "status": WITHHELD, "reason": reason}
