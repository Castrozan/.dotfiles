#!/usr/bin/env python3
"""
Git Reminder Hook
=================
Provides helpful reminders for git operations.
Warns about uncommitted changes, branch state, etc.
"""

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


def has_unstaged_changes() -> bool:
    """Check if there are unstaged changes."""
    code, _ = run_git(["diff", "--quiet"])
    return code != 0


def is_git_repo() -> bool:
    """Check if current directory is in a git repo."""
    code, _ = run_git(["rev-parse", "--is-inside-work-tree"])
    return code == 0


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    command = data.get("tool_input", {}).get("command", "")

    if not command or not command.startswith("git"):
        sys.exit(0)

    if not is_git_repo():
        sys.exit(0)

    messages = []

    # Check for git commit
    if re.search(r"^git\s+commit", command):
        if has_unstaged_changes():
            messages.append("NOTE: You have unstaged changes that won't be included in this commit.")

    # Check for git merge/rebase
    if re.search(r"^git\s+(merge|rebase)", command):
        if has_uncommitted_changes():
            messages.append("WARNING: You have uncommitted changes. Consider stashing or committing first.")
        branch = get_current_branch()
        if branch:
            messages.append(f"Current branch: {branch}")

    # Check for git checkout/switch
    if re.search(r"^git\s+(checkout|switch)", command):
        if has_uncommitted_changes():
            messages.append("NOTE: You have uncommitted changes. They will carry over to the new branch.")

    # Check for git stash pop/apply
    if re.search(r"^git\s+stash\s+(pop|apply)", command):
        if has_uncommitted_changes():
            messages.append("WARNING: You have uncommitted changes. Applying stash may cause conflicts.")

    # Check for pushing to protected branches
    if re.search(r"^git\s+push.*\s+(main|master|prod|production)\b", command):
        messages.append("NOTE: Pushing to protected branch. Ensure CI passes and get approval if required.")

    if messages:
        output = {
            "continue": True,
            "systemMessage": "\n".join(messages)
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
