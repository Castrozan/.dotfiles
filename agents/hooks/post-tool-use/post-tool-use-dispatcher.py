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
    os.path.join(hook_script_directory, "line-count"),
    os.path.join(hook_script_directory, "skill-invocation-marker"),
):
    if os.path.isdir(importable_directory) and importable_directory not in sys.path:
        sys.path.insert(0, importable_directory)

from hook_dispatch import (  # noqa: E402
    CLAUDE_SURFACE,
    OPENCODE_SURFACE,
    HookHandler,
    dispatched_hook_input_or_exit,
    requested_hook_surface,
    run_handlers,
)
from hook_event_output import emit_post_tool_use_outcome  # noqa: E402

POST_TOOL_USE_HANDLERS = [
    HookHandler(
        handler_module_name="record_skill_invocation_handler",
        tool_matcher="Skill",
        surfaces=(CLAUDE_SURFACE, OPENCODE_SURFACE),
    ),
    HookHandler(handler_module_name="auto_format_handler", tool_matcher="Edit|Write"),
    HookHandler(
        handler_module_name="record_edited_source_file_handler",
        tool_matcher="Edit|Write",
    ),
    HookHandler(
        handler_module_name="record_changed_nix_file_handler", tool_matcher="Edit|Write"
    ),
    HookHandler(
        handler_module_name="line_count_limit_guard_handler", tool_matcher="Edit|Write"
    ),
]


def main() -> None:
    hook_input = dispatched_hook_input_or_exit(("PostToolUse",))
    outcome = run_handlers(hook_input, POST_TOOL_USE_HANDLERS, requested_hook_surface())
    emit_post_tool_use_outcome(outcome)
    sys.exit(0)


if __name__ == "__main__":
    main()
