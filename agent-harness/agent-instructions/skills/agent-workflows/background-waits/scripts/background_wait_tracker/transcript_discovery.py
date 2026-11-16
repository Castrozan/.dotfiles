from __future__ import annotations

import mmap
import os
import time

BACKGROUND_LAUNCH_MARKERS = (b'"run_in_background":true', b'"name":"Monitor"')
SECONDS_PER_DAY = 86400


def default_transcripts_root():
    return os.path.expanduser("~/.claude/projects")


def transcripts_modified_within(transcripts_root, since_days):
    oldest_modification_time = time.time() - since_days * SECONDS_PER_DAY
    for directory_path, _directory_names, file_names in os.walk(transcripts_root):
        for file_name in file_names:
            transcript_path = os.path.join(directory_path, file_name)
            if (
                file_name.endswith(".jsonl")
                and os.path.getmtime(transcript_path) >= oldest_modification_time
            ):
                yield transcript_path


def transcript_launches_background_commands(transcript_path):
    if os.path.getsize(transcript_path) == 0:
        return False
    with open(transcript_path, "rb") as transcript_file:
        with mmap.mmap(
            transcript_file.fileno(), 0, access=mmap.ACCESS_READ
        ) as transcript_bytes:
            return any(
                transcript_bytes.find(marker) != -1
                for marker in BACKGROUND_LAUNCH_MARKERS
            )


def recent_transcripts_launching_background_commands(transcripts_root, since_days):
    return [
        transcript_path
        for transcript_path in transcripts_modified_within(transcripts_root, since_days)
        if transcript_launches_background_commands(transcript_path)
    ]
