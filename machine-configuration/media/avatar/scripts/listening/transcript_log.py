import json
import logging
import os
import sys
import time
from datetime import UTC, datetime
from functools import cache
from logging.handlers import RotatingFileHandler
from pathlib import Path

import remote_agent
import speech_segmenter

POLL_SECONDS = 0.25
WAKE_LOG_MAX_BYTES = 5 * 1024 * 1024
WAKE_LOG_BACKUP_COUNT = 2


class _PrivateRotatingFileHandler(RotatingFileHandler):
    def _open(self):
        return open(
            self.baseFilename,
            self.mode,
            encoding=self.encoding,
            errors=self.errors,
            opener=lambda filename, flags: os.open(filename, flags, 0o600),
        )


def wake_log_path():
    state_home = os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state"
    return Path(state_home) / "avatar" / "wake.log"


@cache
def _wake_logger():
    path = wake_log_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.parent.chmod(0o700)
    handler = _PrivateRotatingFileHandler(
        path,
        maxBytes=WAKE_LOG_MAX_BYTES,
        backupCount=WAKE_LOG_BACKUP_COUNT,
        encoding="utf-8",
        errors="backslashreplace",
    )
    logger = logging.Logger("avatar-wake", logging.INFO)
    logger.propagate = False
    logger.addHandler(handler)
    return logger


def report_to_log(line):
    try:
        logger = _wake_logger()
    except OSError as error:
        print(f"Could not open the wake log: {error}", file=sys.stderr, flush=True)
        return
    logger.info(line)


def _report(report, phase, **details):
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "phase": phase,
        "room": os.environ.get(remote_agent.HOST_ENVIRONMENT_VARIABLE),
        **details,
    }
    report(json.dumps(record, ensure_ascii=False))


def report_wake(report, text, segment):
    _report(
        report,
        "wake",
        text=text,
        audio_seconds=len(segment) / (2 * speech_segmenter.SAMPLE_RATE),
    )


def report_conversation(report, entry):
    _report(
        report,
        "conversation",
        text=entry["text"],
        sequence=entry["sequence"],
        source=entry.get("source"),
        speaker=entry.get("speaker"),
        turn_finished=entry.get("turn_finished"),
        speech_ended=entry.get("speech_ended"),
        segment_closed=entry.get("segment_closed"),
        transcription_started=entry.get("transcription_started"),
        transcript_written=entry.get("time"),
    )


def report_addressing(report, phase, **decision):
    _report(report, phase, decision="addressing", **decision)


def report_delivery(report, **delivery):
    _report(report, "delivery", **delivery)


def report_talk(report, action, pane):
    _report(report, "talk", action=action, pane=pane)


def report_speech(report, pane, **speech):
    _report(report, "speech", pane=pane, **speech)


def read_since(path, sequence):
    if not path.exists():
        return []
    entries = []
    with path.open() as transcript:
        for line in transcript:
            if line.endswith("\n"):
                entry = json.loads(line)
                if entry["sequence"] > sequence:
                    entries.append(entry)
    return entries


def last_sequence(path):
    entries = read_since(path, 0)
    return entries[-1]["sequence"] if entries else 0


def append(path, source, text, speaker=None, **details):
    entry = {
        "sequence": last_sequence(path) + 1,
        "time": time.time(),
        "source": source,
        "text": text,
        "speaker": speaker,
        "turn_finished": True,
        **details,
    }
    descriptor = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(descriptor, "a") as transcript:
        transcript.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def wait_since(path, sequence, timeout_seconds):
    deadline = time.monotonic() + timeout_seconds
    while True:
        entries = read_since(path, sequence)
        if entries or time.monotonic() >= deadline:
            return entries
        time.sleep(POLL_SECONDS)
