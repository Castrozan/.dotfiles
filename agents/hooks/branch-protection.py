#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import subprocess
import sys


def run_git_command(args: list[str]) -> tuple[int, str]:
    try:
        result = subprocess.run(
            ["git"] + args, capture_output=True, text=True, timeout=5
        )
        return result.returncode, result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 1, ""


def get_current_branch_name() -> str | None:
    code, output = run_git_command(["branch", "--show-current"])
    return output if code == 0 else None


def is_protected_branch(branch: str) -> bool:
    protected_branch_names = [
        "main",
        "master",
        "production",
        "prod",
        "release",
        "develop",
    ]
    return branch.lower() in protected_branch_names


def get_remote_tracking_branch_and_ahead_status() -> tuple[str | None, bool]:
    code, remote_tracking_branch = run_git_command(
        ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"]
    )
    if code != 0:
        return None, False

    code, commits_ahead_count = run_git_command(["rev-list", "--count", "@{u}..HEAD"])
    is_ahead_of_remote = code == 0 and int(commits_ahead_count or "0") > 0
    return remote_tracking_branch, is_ahead_of_remote


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    command = data.get("tool_input", {}).get("command", "")

    if not command or not command.startswith("git"):
        sys.exit(0)

    current_branch = get_current_branch_name()
    if not current_branch:
        sys.exit(0)

    messages = []

    if re.search(r"^git\s+commit", command):
        if is_protected_branch(current_branch):
            messages.append(
                f"PROTECTED BRANCH: You're committing directly to '{current_branch}'.\n"
                "Consider using a feature branch and PR workflow instead."
            )

    if re.search(r"^git\s+push.*--force", command):
        if is_protected_branch(current_branch):
            output = {
                "continue": True,
                "systemMessage": (
                    f"BLOCKED: Force push to protected branch "
                    f"'{current_branch}' is dangerous.\n"
                    "This can destroy commit history "
                    "for all collaborators.\n"
                    "If you really need this, use: "
                    "git push --force-with-lease"
                ),
            }
            print(json.dumps(output))
            sys.exit(0)

    if re.search(r"^git\s+rebase", command):
        if is_protected_branch(current_branch):
            _, is_ahead_of_remote = get_remote_tracking_branch_and_ahead_status()
            if is_ahead_of_remote:
                messages.append(
                    f"CAUTION: Rebasing '{current_branch}' while ahead of remote.\n"
                    "This may require force push and affect collaborators."
                )

    if re.search(r"^git\s+reset\s+--hard", command):
        if is_protected_branch(current_branch):
            messages.append(
                f"CAUTION: Hard reset on protected branch '{current_branch}'.\n"
                "This discards uncommitted changes permanently."
            )

    if re.search(r"^git\s+merge\s+(?!.*--no-ff)", command):
        if is_protected_branch(current_branch):
            messages.append(
                "TIP: Consider using --no-ff for merges to protected branches.\n"
                "This preserves feature branch history in the commit graph."
            )

    if re.search(r"^git\s+stash\s+(pop|apply)", command):
        code, porcelain_output = run_git_command(["status", "--porcelain"])
        if code == 0 and porcelain_output:
            messages.append(
                "WARNING: You have uncommitted changes. "
                "Applying stash may cause conflicts."
            )

    if messages:
        output = {
            "continue": True,
            "systemMessage": "GIT SAFETY:\n" + "\n".join(messages),
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
