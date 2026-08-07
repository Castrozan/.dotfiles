#!/usr/bin/env python3

from __future__ import annotations

import os
import sys

hook_script_directory = os.path.dirname(os.path.realpath(__file__))
for importable_directory in (
    hook_script_directory,
    os.path.join(os.path.dirname(hook_script_directory), "common"),
):
    if os.path.isdir(importable_directory) and importable_directory not in sys.path:
        sys.path.insert(0, importable_directory)

from hook_dispatch import (  # noqa: E402
    CLAUDE_SURFACE,
    CODEX_SURFACE,
    HookHandler,
    dispatched_hook_input_or_exit,
    requested_hook_surface,
    run_handlers,
)
from hook_event_output import emit_context_injection  # noqa: E402

USER_PROMPT_SUBMIT_HANDLERS = [
    HookHandler(
        handler_module_name="herdr_agent_state_report_handler",
        surfaces=(CLAUDE_SURFACE, CODEX_SURFACE),
    ),
]


def main() -> None:
    hook_input = dispatched_hook_input_or_exit(("UserPromptSubmit",))
    outcome = run_handlers(
        hook_input, USER_PROMPT_SUBMIT_HANDLERS, requested_hook_surface()
    )
    emit_context_injection("UserPromptSubmit", outcome)
    sys.exit(0)


if __name__ == "__main__":
    main()
