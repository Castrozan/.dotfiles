#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

hook_script_directory = Path(__file__).resolve().parent
shared_common_hook_modules_directory = hook_script_directory.parent / "common"
lint_hook_modules_directory = hook_script_directory.parent / "lint"
line_count_hook_modules_directory = hook_script_directory / "line-count"
instructions_skill_invocation_hook_modules_directory = (
    hook_script_directory / "instructions-skill-invocation"
)
for importable_directory in (
    hook_script_directory,
    shared_common_hook_modules_directory,
    lint_hook_modules_directory,
    line_count_hook_modules_directory,
    instructions_skill_invocation_hook_modules_directory,
):
    importable_directory_string = str(importable_directory)
    if importable_directory.is_dir() and importable_directory_string not in sys.path:
        sys.path.insert(0, importable_directory_string)

import auto_format_handler  # noqa: E402
import line_count_limit_guard_handler  # noqa: E402
import nix_rebuild_trigger_handler  # noqa: E402
import record_edited_source_file_handler  # noqa: E402
import record_instructions_skill_invocation_handler  # noqa: E402
from hook_dispatch import (  # noqa: E402
    CLAUDE_SURFACE,
    HookHandler,
    dispatched_hook_input_or_exit,
    requested_hook_surface,
    run_handlers,
)
from hook_event_output import emit_post_tool_use_outcome  # noqa: E402

POST_TOOL_USE_HANDLERS = [
    HookHandler(
        handle=record_instructions_skill_invocation_handler.handle,
        tool_matcher="Skill",
        surfaces=(CLAUDE_SURFACE,),
    ),
    HookHandler(handle=auto_format_handler.handle, tool_matcher="Edit|Write"),
    HookHandler(
        handle=record_edited_source_file_handler.handle, tool_matcher="Edit|Write"
    ),
    HookHandler(handle=nix_rebuild_trigger_handler.handle, tool_matcher="Edit|Write"),
    HookHandler(
        handle=line_count_limit_guard_handler.handle,
        tool_matcher="Edit|Write",
        surfaces=(CLAUDE_SURFACE,),
    ),
]


def main() -> None:
    hook_input = dispatched_hook_input_or_exit(("PostToolUse",))
    outcome = run_handlers(hook_input, POST_TOOL_USE_HANDLERS, requested_hook_surface())
    emit_post_tool_use_outcome(outcome)
    sys.exit(0)


if __name__ == "__main__":
    main()
