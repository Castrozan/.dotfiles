#!/usr/bin/env python3

"""Summon one Servant for an interactive launch and compose its system prompt.

The Servant is a pure function of the session id the launch resolves, so the
same conversation always draws the same one with nothing persisted between runs.

The session-start hook cannot carry the manner: everything a hook injects
arrives as ambient context the harness tells the session not to act on. The
launch wrapper appends this composed file with --append-system-prompt-file, so
the Servant line lands in the session's own instruction surface instead.
"""

from __future__ import annotations

import secrets
import shlex
import sys
from pathlib import Path

module_directory = Path(__file__).resolve().parent
if str(module_directory) not in sys.path:
    sys.path.insert(0, str(module_directory))

from servant_catalog import (  # noqa: E402
    SERVANT_CATALOG,
    select_servant_for_session,
    servant_temporary_directory,
)
from servant_session_id import resolve_session_id  # noqa: E402


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
    servant: dict,
    composed_path: Path,
    display_name: str = "",
    session_id_to_pass: str = "",
) -> list[str]:
    return [
        f"SERVANT_NAME={shlex.quote(servant['name'])}",
        f"SERVANT_CLASS={shlex.quote(servant['class'])}",
        f"SERVANT_MANNER={shlex.quote(servant['manner'])}",
        f"SERVANT_SYSTEM_PROMPT_FILE={shlex.quote(str(composed_path))}",
        f"SERVANT_SESSION_NAME={shlex.quote(display_name)}",
        f"SERVANT_SESSION_ID={shlex.quote(session_id_to_pass)}",
    ]


def main() -> int:
    base_prompt_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/dev/null")
    launch_arguments = sys.argv[2:]
    try:
        session_id, minted_here = resolve_session_id(launch_arguments, Path.cwd())
    except OSError:
        session_id, minted_here = None, False
    servant = (
        select_servant_for_session(session_id)
        if session_id
        else secrets.choice(SERVANT_CATALOG)
    )
    composed_path = compose_system_prompt_file(base_prompt_path, servant)
    export_lines = shell_export_lines(
        servant,
        composed_path,
        session_display_name(servant, launch_arguments),
        session_id if minted_here else "",
    )
    for export_line in export_lines:
        print(export_line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
