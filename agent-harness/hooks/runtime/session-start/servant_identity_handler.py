#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

hook_script_directory = Path(__file__).resolve().parent
shared_common_hook_modules_directory = hook_script_directory.parent / "common"
for importable_directory in (
    hook_script_directory,
    shared_common_hook_modules_directory,
):
    importable_directory_string = str(importable_directory)
    if importable_directory.is_dir() and importable_directory_string not in sys.path:
        sys.path.insert(0, importable_directory_string)

from hook_dispatch import HandlerResult  # noqa: E402
from interactive_session_detection import (  # noqa: E402
    is_keyboard_driven_interactive_session,
)
from servant_catalog import (  # noqa: E402
    read_servant_identity,
    select_servant_for_session,
    write_servant_identity,
)


def format_servant_context(servant: dict) -> str:
    name = servant.get("name", "a nameless Heroic Spirit")
    servant_class = servant.get("class", "")
    catchphrase = servant.get("catchphrase", "")
    manner = servant.get("manner", "")
    titling = f" ({servant_class})" if servant_class else ""
    lines = [f"You are summoned as {name}{titling}."]
    if catchphrase:
        lines.append(f'"{catchphrase}"')
    if manner:
        lines.append(manner)
    return "SERVANT:\n" + "\n".join(lines)


def handle(hook_input: dict):
    if not is_keyboard_driven_interactive_session():
        return None

    session_id = hook_input.get("session_id", "") or ""
    existing_identity = read_servant_identity(session_id)
    if isinstance(existing_identity, dict) and existing_identity.get("name"):
        servant = existing_identity
    else:
        servant = select_servant_for_session(session_id)
        write_servant_identity(session_id, servant)
    return HandlerResult(additional_context=format_servant_context(servant))
