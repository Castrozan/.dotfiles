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

from interactive_session_detection import (  # noqa: E402
    is_keyboard_driven_interactive_session,
)
from servant_catalog import (  # noqa: E402
    read_servant_identity,
    select_servant_for_session,
    servant_summoned_at_launch,
    write_servant_identity,
)


def servant_for_session(session_id: str) -> dict:
    """Who this session is, preferring a choice already made over a fresh draw.

    A Servant the launch wrapper summoned outranks a stored one, so a relaunch
    in the same pane records the identity the session's own system prompt
    carries rather than the previous launch's.
    """
    summoned_at_launch = servant_summoned_at_launch()
    if summoned_at_launch is not None:
        return summoned_at_launch
    stored_identity = read_servant_identity(session_id)
    if isinstance(stored_identity, dict) and stored_identity.get("name"):
        return stored_identity
    return select_servant_for_session(session_id)


def handle(hook_input: dict):
    """Record the session's Servant for the statusline, and inject nothing.

    The manner reaches the session through the launch wrapper's appended system
    prompt. A hook cannot carry it: additionalContext arrives as ambient context
    the session is told not to act on, which is why it read as a label rather
    than an identity.
    """
    if not is_keyboard_driven_interactive_session():
        return None
    session_id = hook_input.get("session_id", "") or ""
    write_servant_identity(session_id, servant_for_session(session_id))
    return None
