from __future__ import annotations

import os

from dotfiles_repository_scope import repository_is_personal_tooling
from hook_dispatch import HandlerResult


def handle(hook_input: dict):
    directories = (
        hook_input.get("cwd", ""),
        os.environ.get("AGENT_EVALS_SOURCE_ROOT", ""),
    )
    if not any(repository_is_personal_tooling(directory) for directory in directories):
        return None
    decision = (
        "deny"
        if hook_input.get("hook_event_name") == "PreToolUse"
        or hook_input.get("tool_name")
        else "block"
    )
    return HandlerResult(
        decision=decision,
        reason="Claude Code is disabled for dotfiles and its personal tooling repositories. Use Codex.",
    )
