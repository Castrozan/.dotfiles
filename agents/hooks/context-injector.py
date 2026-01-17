#!/usr/bin/env python3
"""
Context Injector Hook
=====================
Injects helpful context and reminders based on the current environment.
Runs on UserPromptSubmit to provide relevant information at session start.

This hook checks for various conditions and injects relevant context:
- Project-specific reminders from .claude/CONTEXT.md
- Git branch and status
- Environment-specific notes
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def run_git(args: list[str]) -> tuple[int, str]:
    """Run a git command and return (exit_code, output)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode, result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 1, ""


def get_git_context() -> str | None:
    """Get git status context."""
    code, branch = run_git(["branch", "--show-current"])
    if code != 0:
        return None

    code, status = run_git(["status", "--porcelain"])
    if code != 0:
        return None

    changes = len(status.split("\n")) if status else 0

    if changes > 0:
        return f"Git: branch '{branch}', {changes} uncommitted change(s)"
    return f"Git: branch '{branch}', clean"


def get_project_context() -> str | None:
    """Read project-specific context from .claude/CONTEXT.md."""
    context_file = Path(".claude/CONTEXT.md")
    if context_file.exists():
        try:
            content = context_file.read_text().strip()
            if content:
                return f"Project context:\n{content}"
        except Exception:
            pass
    return None


def get_environment_context() -> list[str]:
    """Get environment-specific context."""
    context = []

    # Check for common development indicators
    if Path("package.json").exists():
        context.append("Node.js project detected")
    if Path("Cargo.toml").exists():
        context.append("Rust project detected")
    if Path("flake.nix").exists():
        context.append("Nix flake project - use nix develop for shell")
    if Path("devenv.nix").exists():
        context.append("devenv project - use devenv shell")

    return context


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    # Only inject context for new sessions (first prompt)
    # We can detect this by checking if there's minimal conversation history
    # For now, always inject but keep it minimal

    context_parts = []

    # Git context
    git_ctx = get_git_context()
    if git_ctx:
        context_parts.append(git_ctx)

    # Project context
    project_ctx = get_project_context()
    if project_ctx:
        context_parts.append(project_ctx)

    # Environment context
    env_ctx = get_environment_context()
    if env_ctx:
        context_parts.extend(env_ctx)

    if context_parts:
        output = {
            "decision": "continue",
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "\n".join(context_parts)
            }
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
