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

import compaction_context_recovery_handler  # noqa: E402
import herdr_agent_session_report_handler  # noqa: E402
import session_context_handler  # noqa: E402
from hook_dispatch import (  # noqa: E402
    CLAUDE_SURFACE,
    CODEX_SURFACE,
    HookHandler,
    dispatched_hook_input_or_exit,
    requested_hook_surface,
    run_handlers,
)
from hook_event_output import emit_context_injection  # noqa: E402

SESSION_START_HANDLERS = [
    HookHandler(handle=session_context_handler.handle, surfaces=(CLAUDE_SURFACE,)),
    HookHandler(handle=compaction_context_recovery_handler.handle),
    HookHandler(
        handle=herdr_agent_session_report_handler.handle,
        surfaces=(CLAUDE_SURFACE, CODEX_SURFACE),
    ),
]


def main() -> None:
    hook_input = dispatched_hook_input_or_exit(("SessionStart",))
    outcome = run_handlers(hook_input, SESSION_START_HANDLERS, requested_hook_surface())
    emit_context_injection("SessionStart", outcome)
    sys.exit(0)


if __name__ == "__main__":
    main()
