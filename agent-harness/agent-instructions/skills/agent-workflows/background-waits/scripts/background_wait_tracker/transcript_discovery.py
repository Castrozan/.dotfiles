from __future__ import annotations

import os
import subprocess
import time

BACKGROUND_LAUNCH_MARKERS = ('"run_in_background":true', '"name":"Monitor"')
SECONDS_PER_DAY = 86400
RIPGREP_NO_MATCH_EXIT_CODE = 1


def default_transcripts_root():
    return os.path.expanduser("~/.claude/projects")


def transcripts_launching_background_commands(transcripts_root):
    marker_arguments = [
        argument
        for marker in BACKGROUND_LAUNCH_MARKERS
        for argument in ("--regexp", marker)
    ]
    completed = subprocess.run(
        [
            "rg",
            "--files-with-matches",
            "--no-messages",
            "--fixed-strings",
            "--glob",
            "*.jsonl",
            *marker_arguments,
            str(transcripts_root),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode not in (0, RIPGREP_NO_MATCH_EXIT_CODE):
        raise RuntimeError(f"rg failed over {transcripts_root}: {completed.stderr}")
    return completed.stdout.splitlines()


def recent_transcripts_launching_background_commands(transcripts_root, since_days):
    oldest_modification_time = time.time() - since_days * SECONDS_PER_DAY
    return [
        transcript_path
        for transcript_path in transcripts_launching_background_commands(
            transcripts_root
        )
        if os.path.getmtime(transcript_path) >= oldest_modification_time
    ]
