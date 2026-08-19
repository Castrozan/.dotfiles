#!/usr/bin/env python3

"""Summon one Servant for an interactive launch and compose its system prompt.

The session-start hook cannot carry the manner: everything a hook injects
arrives as ambient context the harness tells the session not to act on. The
launch wrapper appends this composed file with --append-system-prompt-file, so
the Servant line lands in the session's own instruction surface instead.
"""

from __future__ import annotations

import json
import re
import secrets
import shlex
import sys
from pathlib import Path

module_directory = Path(__file__).resolve().parent
if str(module_directory) not in sys.path:
    sys.path.insert(0, str(module_directory))

from servant_catalog import (  # noqa: E402
    SERVANT_CATALOG,
    read_servant_identity,
    select_servant_for_session,
    servant_temporary_directory,
)

RESUME_FLAG_TOKENS = {"-c", "--continue", "-r", "--resume"}
_SESSION_ID_PATTERN = re.compile(r"^[0-9a-fA-F-]{20,}$")


def servant_system_prompt_line(servant: dict) -> str:
    return (
        f"<servant>You are {servant['name']}. {servant['manner']} "
        "Carry that manner as a light flavour of voice only, in at most a phrase "
        "per reply. It never changes your technical accuracy, your reasoning, the "
        "output shape a request asks for, or any other instruction you hold."
        "</servant>"
    )


def compose_system_prompt_file(base_prompt_path: Path, servant: dict) -> Path:
    composed_path = (
        servant_temporary_directory()
        / f"claude-servant-system-prompt-{secrets.token_hex(6)}.md"
    )
    base_prompt_text = ""
    if base_prompt_path.is_file():
        base_prompt_text = base_prompt_path.read_text(encoding="utf-8")
    composed_path.write_text(
        base_prompt_text.rstrip("\n") + "\n\n" + servant_system_prompt_line(servant),
        encoding="utf-8",
    )
    return composed_path


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


def resolve_servant_for_launch(
    launch_arguments: list[str], cwd: Path, projects_root: Path | None = None
) -> dict | None:
    """The Servant a resumed session should keep, or None for a fresh launch.

    A hook re-firing mid-process (compaction) was never the risk here: the wrapper
    is what runs again on --resume/--continue, as a brand new process, before any
    session id is resolved - and it drew a fresh random Servant every time,
    overwriting the composed system prompt and the stored identity on every
    resume. This resolves the session being continued first so the same Servant
    carries across relaunches instead.
    """
    if not is_resume_shaped_launch(launch_arguments):
        return None
    session_id = explicit_resume_session_id(launch_arguments)
    if session_id is None:
        session_id = most_recent_transcript_session_id_for_cwd(cwd, projects_root)
    if session_id is None:
        return None
    return read_servant_identity(session_id) or select_servant_for_session(session_id)


def session_display_name(servant: dict, launch_arguments: list[str]) -> str:
    """The peer-session name, keeping the workspace and adding the Servant.

    Claude Code derives a session name from the working directory, which is what
    another agent sees when it lists peers. Appending rather than replacing keeps
    the workspace legible while making the session addressable by Servant. A name
    the human passed themselves always wins, so this yields an empty string then.
    """
    if any(argument in ("-n", "--name") for argument in launch_arguments):
        return ""
    workspace_name = Path.cwd().name
    if not workspace_name:
        return servant["name"]
    return f"{workspace_name} ⋅ {servant['name']}"


def shell_export_lines(
    servant: dict, composed_path: Path, display_name: str = ""
) -> list[str]:
    return [
        f"SERVANT_NAME={shlex.quote(servant['name'])}",
        f"SERVANT_CLASS={shlex.quote(servant['class'])}",
        f"SERVANT_MANNER={shlex.quote(servant['manner'])}",
        f"SERVANT_SYSTEM_PROMPT_FILE={shlex.quote(str(composed_path))}",
        f"SERVANT_SESSION_NAME={shlex.quote(display_name)}",
    ]


def main() -> int:
    base_prompt_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/dev/null")
    launch_arguments = sys.argv[2:]
    try:
        servant = resolve_servant_for_launch(launch_arguments, Path.cwd())
    except OSError:
        servant = None
    if servant is None:
        servant = secrets.choice(SERVANT_CATALOG)
    composed_path = compose_system_prompt_file(base_prompt_path, servant)
    display_name = session_display_name(servant, launch_arguments)
    for export_line in shell_export_lines(servant, composed_path, display_name):
        print(export_line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
