#!/usr/bin/env python3
"""worktree-reminder.py - Suggest worktrees for parallel work on different branches."""

import json
import os
import re
import subprocess
import sys


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


def get_current_branch() -> str | None:
    """Get current git branch name."""
    code, output = run_git(["branch", "--show-current"])
    return output if code == 0 else None


def has_uncommitted_changes() -> bool:
    """Check if there are uncommitted changes."""
    code, output = run_git(["status", "--porcelain"])
    return code == 0 and bool(output)


def is_in_worktree() -> bool:
    """Check if we're in a worktree (not main repo)."""
    code, output = run_git(["rev-parse", "--git-common-dir"])
    if code != 0:
        return False
    # If git-common-dir differs from git-dir, we're in a worktree
    code2, git_dir = run_git(["rev-parse", "--git-dir"])
    return code2 == 0 and output != git_dir


def count_existing_worktrees() -> int:
    """Count existing worktrees."""
    code, output = run_git(["worktree", "list", "--porcelain"])
    if code != 0:
        return 0
    return output.count("worktree ")


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    command = data.get("tool_input", {}).get("command", "")

    if not command:
        sys.exit(0)

    # Patterns that suggest switching branches for parallel work
    branch_switch_patterns = [
        r"^git\s+checkout\s+-b\s+\S+",      # Creating new branch
        r"^git\s+switch\s+-c\s+\S+",        # Creating new branch (newer syntax)
        r"^git\s+checkout\s+(?!-)\S+",      # Switching to existing branch
        r"^git\s+switch\s+(?!-)\S+",        # Switching (newer syntax)
    ]

    is_branch_operation = any(
        re.search(pattern, command) for pattern in branch_switch_patterns
    )

    if not is_branch_operation:
        sys.exit(0)

    # Skip if already in a worktree
    if is_in_worktree():
        sys.exit(0)

    messages = []
    current_branch = get_current_branch()

    # Warn if switching with uncommitted changes
    if has_uncommitted_changes():
        messages.append(
            "You have uncommitted changes that may be affected by branch switching."
        )

    # Suggest worktrees for parallel work
    worktree_count = count_existing_worktrees()
    if worktree_count <= 1:  # Main repo counts as 1
        messages.append(
            "Consider using /worktrees skill for parallel development:\n"
            "  - Keep this branch's work in progress\n"
            "  - Work on new feature in isolated directory\n"
            "  - Avoid stash/switch dance"
        )
    else:
        messages.append(
            f"You have {worktree_count - 1} active worktree(s). "
            "Use /worktrees to manage or create new ones."
        )

    if messages:
        output = {
            "continue": True,
            "systemMessage": "GIT WORKTREE TIP:\n" + "\n".join(messages)
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
