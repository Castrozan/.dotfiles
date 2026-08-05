#!/usr/bin/env python3

from __future__ import annotations

import os
import sys

hook_script_directory = os.path.dirname(os.path.realpath(__file__))
shared_common_hook_modules_directory = os.path.join(
    os.path.dirname(hook_script_directory), "common"
)
human_facing_reply_modules_directory = os.path.join(
    shared_common_hook_modules_directory, "human_facing_reply"
)
for importable_directory in (
    hook_script_directory,
    shared_common_hook_modules_directory,
    human_facing_reply_modules_directory,
):
    if os.path.isdir(importable_directory) and importable_directory not in sys.path:
        sys.path.insert(0, importable_directory)

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
