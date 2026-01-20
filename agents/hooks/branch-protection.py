#!/usr/bin/env python3
"""branch-protection.py - Extra warnings for operations on protected branches."""

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


def is_protected_branch(branch: str) -> bool:
    """Check if branch is protected."""
    protected = ["main", "master", "production", "prod", "release", "develop"]
    return branch.lower() in protected


def get_remote_tracking_info() -> tuple[str | None, bool]:
    """Get remote tracking branch and whether we're ahead/behind."""
    code, output = run_git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    if code != 0:
        return None, False

    # Check if ahead of remote
    code2, ahead = run_git(["rev-list", "--count", "@{u}..HEAD"])
    return output, (code2 == 0 and int(ahead or "0") > 0)


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    command = data.get("tool_input", {}).get("command", "")

    if not command or not command.startswith("git"):
        sys.exit(0)

    current_branch = get_current_branch()
    if not current_branch:
        sys.exit(0)

    messages = []

    # Check for direct commits on protected branch
    if re.search(r"^git\s+commit", command):
        if is_protected_branch(current_branch):
            messages.append(
                f"PROTECTED BRANCH: You're committing directly to '{current_branch}'.\n"
                "Consider using a feature branch and PR workflow instead."
            )

    # Check for force push attempts
    if re.search(r"^git\s+push.*--force", command):
        if is_protected_branch(current_branch):
            # Block force push to protected branches
            output = {
                "continue": True,
                "systemMessage": (
                    f"BLOCKED: Force push to protected branch '{current_branch}' is dangerous.\n"
                    "This can destroy commit history for all collaborators.\n"
                    "If you really need this, use: git push --force-with-lease"
                )
            }
            print(json.dumps(output))
            sys.exit(0)

    # Check for rebasing protected branch
    if re.search(r"^git\s+rebase", command):
        if is_protected_branch(current_branch):
            remote_branch, is_ahead = get_remote_tracking_info()
            if remote_branch and is_ahead:
                messages.append(
                    f"CAUTION: Rebasing '{current_branch}' while ahead of remote.\n"
                    "This may require force push and affect collaborators."
                )

    # Check for hard reset on protected branch
    if re.search(r"^git\s+reset\s+--hard", command):
        if is_protected_branch(current_branch):
            messages.append(
                f"CAUTION: Hard reset on protected branch '{current_branch}'.\n"
                "This discards uncommitted changes permanently."
            )

    # Check for merge without --no-ff on protected branches
    if re.search(r"^git\s+merge\s+(?!.*--no-ff)", command):
        if is_protected_branch(current_branch):
            messages.append(
                "TIP: Consider using --no-ff for merges to protected branches.\n"
                "This preserves feature branch history in the commit graph."
            )

    # Check for stash pop/apply with uncommitted changes
    if re.search(r"^git\s+stash\s+(pop|apply)", command):
        code, porcelain = run_git(["status", "--porcelain"])
        if code == 0 and porcelain:
            messages.append(
                "WARNING: You have uncommitted changes. Applying stash may cause conflicts."
            )

    if messages:
        output = {
            "continue": True,
            "systemMessage": "GIT SAFETY:\n" + "\n".join(messages)
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
