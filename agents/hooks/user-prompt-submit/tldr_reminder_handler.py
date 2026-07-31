#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

hook_script_directory = Path(__file__).resolve().parent
shared_common_hook_modules_directory = hook_script_directory.parent / "common"
human_facing_reply_modules_directory = (
    shared_common_hook_modules_directory / "human_facing_reply"
)
for importable_directory in (
    hook_script_directory,
    shared_common_hook_modules_directory,
    human_facing_reply_modules_directory,
):
    importable_directory_string = str(importable_directory)
    if importable_directory.is_dir() and importable_directory_string not in sys.path:
        sys.path.insert(0, importable_directory_string)

from hook_dispatch import HandlerResult  # noqa: E402
from interactive_reply_reminder_state import (  # noqa: E402
    record_reply_reminder_injected,
    reply_reminder_should_be_injected,
)
from interactive_session_detection import (  # noqa: E402
    is_keyboard_driven_interactive_session,
)
from reply_rule_rendering import rendered_reply_reminder  # noqa: E402


def handle(hook_input: dict):
    if not is_keyboard_driven_interactive_session():
        return None
    session_id = hook_input.get("session_id") or ""
    if not reply_reminder_should_be_injected(session_id):
        return None
    record_reply_reminder_injected(session_id)
    return HandlerResult(additional_context=rendered_reply_reminder())
