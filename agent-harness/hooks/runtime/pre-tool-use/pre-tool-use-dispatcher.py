#!/usr/bin/env python3

from __future__ import annotations

import os
import sys

hook_script_directory = os.path.dirname(os.path.realpath(__file__))
importable_directories = [
    hook_script_directory,
    os.path.join(os.path.dirname(hook_script_directory), "common"),
]
importable_directories.extend(
    child_entry.path
    for child_entry in os.scandir(hook_script_directory)
    if child_entry.is_dir()
)
for importable_directory in importable_directories:
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
from hook_event_output import emit_pretooluse_decision  # noqa: E402

PRE_TOOL_USE_HANDLERS = [
    HookHandler(
        handler_module_name="prohibited_command_guard_handler", tool_matcher=None
    ),
    HookHandler(
        handler_module_name="destructive_command_guard_handler", tool_matcher="Bash"
    ),
    HookHandler(
        handler_module_name="prohibited_words_guard_handler", tool_matcher=None
    ),
    HookHandler(
        handler_module_name="worktree_location_guard_handler", tool_matcher="Bash"
    ),
    HookHandler(
        handler_module_name="workspace_directory_injector_handler",
        tool_matcher="Bash",
        surfaces=(CLAUDE_SURFACE,),
    ),
    HookHandler(
        handler_module_name="background_bash_anti_pattern_validator_handler",
        tool_matcher="Bash",
        surfaces=(CLAUDE_SURFACE, OPENCODE_SURFACE),
    ),
    HookHandler(
        handler_module_name="codex_sandbox_downgrade_guard_handler",
        tool_matcher="mcp__codex__codex",
        surfaces=(CLAUDE_SURFACE,),
    ),
    HookHandler(
        handler_module_name="blocked_skill_invocation_guard_handler",
        tool_matcher="Skill",
        surfaces=(CLAUDE_SURFACE, OPENCODE_SURFACE),
    ),
    HookHandler(
        handler_module_name="url_to_skill_router_handler",
        tool_matcher="WebFetch",
        surfaces=(CLAUDE_SURFACE, OPENCODE_SURFACE),
    ),
    HookHandler(
        handler_module_name="monitor_streaming_pattern_validator_handler",
        tool_matcher="Monitor",
        surfaces=(CLAUDE_SURFACE,),
    ),
    HookHandler(
        handler_module_name="agent_instruction_file_authoring_router_handler",
        tool_matcher="Write|Edit",
    ),
    HookHandler(
        handler_module_name="documentation_authoring_router_handler",
        tool_matcher="Write|Edit",
    ),
    HookHandler(
        handler_module_name="subagent_budget_guard_handler",
        tool_matcher="Agent",
        surfaces=(CLAUDE_SURFACE, OPENCODE_SURFACE),
    ),
]


def main() -> None:
    hook_input = dispatched_hook_input_or_exit(("PreToolUse",))
    outcome = run_handlers(hook_input, PRE_TOOL_USE_HANDLERS, requested_hook_surface())
    emit_pretooluse_decision(outcome)
    sys.exit(0)


if __name__ == "__main__":
    main()
