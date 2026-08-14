#!/usr/bin/env python3

from __future__ import annotations

import os
import sys

hook_script_directory = os.path.dirname(os.path.realpath(__file__))
hooks_root_directory = os.path.dirname(hook_script_directory)
for importable_directory in (
    hook_script_directory,
    os.path.join(hooks_root_directory, "common"),
    os.path.join(hooks_root_directory, "lint"),
    os.path.join(hooks_root_directory, "nix-rebuild"),
):
    if os.path.isdir(importable_directory) and importable_directory not in sys.path:
        sys.path.insert(0, importable_directory)

from hook_dispatch import (  # noqa: E402
    CLAUDE_SURFACE,
    CODEX_SURFACE,
    OPENCODE_SURFACE,
    PI_SURFACE,
    HookHandler,
    dispatched_hook_input_or_exit,
    requested_hook_surface,
    run_handlers,
)
from hook_event_output import emit_stop_decision  # noqa: E402

STOP_HANDLERS = [
    HookHandler(handler_module_name="lint_turn_review_handler"),
    HookHandler(handler_module_name="nix_rebuild_reminder_handler"),
    HookHandler(
        handler_module_name="end_of_turn_format_guard_handler",
        surfaces=(CLAUDE_SURFACE, CODEX_SURFACE, OPENCODE_SURFACE, PI_SURFACE),
    ),
    HookHandler(
        handler_module_name="herdr_agent_session_report_handler",
        surfaces=(CLAUDE_SURFACE, CODEX_SURFACE),
    ),
]


def main() -> None:
    hook_input = dispatched_hook_input_or_exit(("Stop", "SubagentStop"))
    outcome = run_handlers(hook_input, STOP_HANDLERS, requested_hook_surface())
    emit_stop_decision(outcome)
    sys.exit(0)


if __name__ == "__main__":
    main()
