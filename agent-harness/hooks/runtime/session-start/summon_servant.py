#!/usr/bin/env python3

"""Summon one Servant for an interactive launch and compose its system prompt.

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
    servant_temporary_directory,
)


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


def shell_export_lines(servant: dict, composed_path: Path) -> list[str]:
    return [
        f"SERVANT_NAME={shlex.quote(servant['name'])}",
        f"SERVANT_CLASS={shlex.quote(servant['class'])}",
        f"SERVANT_MANNER={shlex.quote(servant['manner'])}",
        f"SERVANT_SYSTEM_PROMPT_FILE={shlex.quote(str(composed_path))}",
    ]


def main() -> int:
    base_prompt_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/dev/null")
    servant = secrets.choice(SERVANT_CATALOG)
    composed_path = compose_system_prompt_file(base_prompt_path, servant)
    for export_line in shell_export_lines(servant, composed_path):
        print(export_line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
