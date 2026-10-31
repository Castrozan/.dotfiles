import json
import os
import time

POLL_SECONDS = 0.25


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


def append(path, source, text):
    entry = {
        "sequence": last_sequence(path) + 1,
        "time": time.time(),
        "source": source,
        "text": text,
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
