#!/usr/bin/env python3

"""Which session id a claude launch will run under, resolved before it starts.

The Servant is derived from that id, so the launch wrapper has to know it up
front: a fresh launch mints one here and passes it through as --session-id, and
a resume resolves the id it is continuing instead. That is what keeps a
conversation on one Servant across relaunches without persisting anything.
"""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

RESUME_FLAG_TOKENS = {"-c", "--continue", "-r", "--resume"}
_SESSION_ID_PATTERN = re.compile(r"^[0-9a-fA-F-]{20,}$")


def is_resume_shaped_launch(launch_arguments: list[str]) -> bool:
    return any(argument in RESUME_FLAG_TOKENS for argument in launch_arguments)


def explicit_resume_session_id(launch_arguments: list[str]) -> str | None:
    """The session id named right on the command line, when there is one.

    -c/--continue and a bare -r/--resume (interactive picker) never carry an id
    here; the caller falls back to the transcript scan for those.
    """
    for index, argument in enumerate(launch_arguments):
        if argument not in ("-r", "--resume"):
            continue
        following = (
            launch_arguments[index + 1] if index + 1 < len(launch_arguments) else None
        )
        if (
            following
            and not following.startswith("-")
            and _SESSION_ID_PATTERN.match(following)
        ):
            return following
    return None


def _session_id_of_matching_transcript(
    transcript_path: Path, target_cwd: str, lines_to_check: int = 30
) -> str | None:
    try:
        with transcript_path.open("r", encoding="utf-8") as transcript_file:
            for _ in range(lines_to_check):
                line = transcript_file.readline()
                if not line:
                    break
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if record.get("cwd") == target_cwd:
                    return record.get("sessionId")
    except OSError:
        return None
    return None


def most_recent_transcript_session_id_for_cwd(
    cwd: Path, projects_root: Path | None = None
) -> str | None:
    """The session -c/--continue would resume, read from Claude Code's own transcripts.

    Re-deriving Claude Code's project-directory name encoding would be fragile, so
    this matches on the cwd every transcript already records instead, newest
    transcript first - the same "most recent conversation in this directory" -c
    itself resolves to.
    """
    root = projects_root or (Path.home() / ".claude" / "projects")
    if not root.is_dir():
        return None
    transcript_paths = sorted(
        root.glob("*/*.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True
    )
    target_cwd = str(cwd)
    for transcript_path in transcript_paths:
        session_id = _session_id_of_matching_transcript(transcript_path, target_cwd)
        if session_id is not None:
            return session_id
    return None


def human_supplied_session_id(launch_arguments: list[str]) -> str | None:
    for index, argument in enumerate(launch_arguments):
        if argument == "--session-id" and index + 1 < len(launch_arguments):
            return launch_arguments[index + 1]
    return None


def resolve_session_id(
    launch_arguments: list[str], cwd: Path, projects_root: Path | None = None
) -> tuple[str | None, bool]:
    """The session id this launch will run under, and whether we minted it.

    A resume never mints: it resolves the id already being continued, and yields
    None when nothing matches, which leaves the caller to draw at random for a
    session whose identity it cannot know.
    """
    supplied_session_id = human_supplied_session_id(launch_arguments)
    if supplied_session_id:
        return supplied_session_id, False
    if is_resume_shaped_launch(launch_arguments):
        resumed_session_id = explicit_resume_session_id(
            launch_arguments
        ) or most_recent_transcript_session_id_for_cwd(cwd, projects_root)
        return resumed_session_id, False
    return str(uuid.uuid4()), True
