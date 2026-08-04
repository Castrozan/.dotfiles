#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

hook_script_directory = Path(__file__).resolve().parent
shared_common_hook_modules_directory = hook_script_directory.parent / "common"
importable_directories = [hook_script_directory, shared_common_hook_modules_directory]
importable_directories.extend(
    child_directory
    for child_directory in hook_script_directory.iterdir()
    if child_directory.is_dir()
)
for importable_directory in importable_directories:
    importable_directory_string = str(importable_directory)
    if importable_directory.is_dir() and importable_directory_string not in sys.path:
        sys.path.insert(0, importable_directory_string)

import agent_instruction_file_authoring_router_handler  # noqa: E402
import background_bash_anti_pattern_validator_handler  # noqa: E402
import blocked_skill_invocation_guard_handler  # noqa: E402
import codex_sandbox_downgrade_guard_handler  # noqa: E402
import documentation_authoring_router_handler  # noqa: E402
import monitor_streaming_pattern_validator_handler  # noqa: E402
import prohibited_command_guard_handler  # noqa: E402
import prohibited_words_guard_handler  # noqa: E402
import subagent_budget_guard_handler  # noqa: E402
import url_to_skill_router_handler  # noqa: E402
import workspace_directory_injector_handler  # noqa: E402
import worktree_location_guard_handler  # noqa: E402
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
    HookHandler(handle=prohibited_command_guard_handler.handle, tool_matcher=None),
    HookHandler(handle=prohibited_words_guard_handler.handle, tool_matcher=None),
    HookHandler(handle=worktree_location_guard_handler.handle, tool_matcher="Bash"),
    HookHandler(
        handle=workspace_directory_injector_handler.handle,
        tool_matcher="Bash",
        surfaces=(CLAUDE_SURFACE,),
    ),
    HookHandler(
        handle=background_bash_anti_pattern_validator_handler.handle,
        tool_matcher="Bash",
        surfaces=(CLAUDE_SURFACE,),
    ),
    HookHandler(
        handle=codex_sandbox_downgrade_guard_handler.handle,
        tool_matcher="mcp__codex__codex",
        surfaces=(CLAUDE_SURFACE,),
    ),
    HookHandler(
        handle=blocked_skill_invocation_guard_handler.handle,
        tool_matcher="Skill",
        surfaces=(CLAUDE_SURFACE, OPENCODE_SURFACE),
    ),
    HookHandler(
        handle=url_to_skill_router_handler.handle,
        tool_matcher="WebFetch",
        surfaces=(CLAUDE_SURFACE, OPENCODE_SURFACE),
    ),
    HookHandler(
        handle=monitor_streaming_pattern_validator_handler.handle,
        tool_matcher="Monitor",
        surfaces=(CLAUDE_SURFACE,),
    ),
    HookHandler(
        handle=agent_instruction_file_authoring_router_handler.handle,
        tool_matcher="Write|Edit",
    ),
    HookHandler(
        handle=documentation_authoring_router_handler.handle,
        tool_matcher="Write|Edit",
    ),
    HookHandler(
        handle=subagent_budget_guard_handler.handle,
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
