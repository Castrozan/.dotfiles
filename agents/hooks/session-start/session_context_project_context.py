"""Detect project-level context markers in the current working directory."""

from __future__ import annotations

import os

from session_context_command_runner import run_cmd


def check_project_context() -> list[str]:
    context_files = []
    cwd = os.getcwd()

    if os.path.exists(os.path.join(cwd, "CLAUDE.md")):
        context_files.append("CLAUDE.md (project instructions)")

    if os.path.exists(os.path.join(cwd, ".claude", "settings.json")):
        context_files.append(".claude/settings.json (project hooks)")

    code, worktrees = run_cmd(["git", "worktree", "list", "--porcelain"])
    if code == 0:
        worktree_count = worktrees.count("worktree ") - 1
        if worktree_count > 0:
            context_files.append(f"{worktree_count} active worktree(s)")

    code, todos = run_cmd(
        ["git", "log", "-5", "--format=%s", "--grep=TODO\\|FIXME\\|WIP"]
    )
    if code == 0 and todos:
        context_files.append("Recent WIP/TODO commits detected")

    return context_files
