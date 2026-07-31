#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

hook_script_directory = Path(__file__).resolve().parent
shared_common_hook_modules_directory = hook_script_directory.parent / "common"
lint_hook_modules_directory = hook_script_directory.parent / "lint"
for importable_directory in (
    hook_script_directory,
    shared_common_hook_modules_directory,
    lint_hook_modules_directory,
):
    importable_directory_string = str(importable_directory)
    if importable_directory.is_dir() and importable_directory_string not in sys.path:
        sys.path.insert(0, importable_directory_string)

import end_of_turn_format_guard_handler  # noqa: E402
import herdr_agent_session_report_handler  # noqa: E402
import lint_turn_review_handler  # noqa: E402
from hook_dispatch import (  # noqa: E402
    CLAUDE_SURFACE,
    HookHandler,
    dispatched_hook_input_or_exit,
    requested_hook_surface,
    run_handlers,
)
from hook_event_output import emit_stop_decision  # noqa: E402

STOP_HANDLERS = [
    HookHandler(handle=lint_turn_review_handler.handle),
    HookHandler(
        handle=end_of_turn_format_guard_handler.handle, surfaces=(CLAUDE_SURFACE,)
    ),
    HookHandler(handle=herdr_agent_session_report_handler.handle),
]


def main() -> None:
    hook_input = dispatched_hook_input_or_exit(("Stop", "SubagentStop"))
    outcome = run_handlers(hook_input, STOP_HANDLERS, requested_hook_surface())
    emit_stop_decision(outcome)
    sys.exit(0)


if __name__ == "__main__":
    main()
