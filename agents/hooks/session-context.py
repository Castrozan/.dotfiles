#!/usr/bin/env python3
"""session-context.py - Show relevant context at session start."""

import json
import os
import subprocess
import sys
from datetime import datetime


def run_cmd(args: list[str], timeout: int = 5) -> tuple[int, str]:
    """Run a command and return (exit_code, output)."""
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 1, ""


def get_git_status() -> dict:
    """Get git repository status."""
    code, _ = run_cmd(["git", "rev-parse", "--is-inside-work-tree"])
    if code != 0:
        return {"is_repo": False}

    status = {"is_repo": True}

    # Current branch
    code, branch = run_cmd(["git", "branch", "--show-current"])
    if code == 0:
        status["branch"] = branch

    # Check for uncommitted changes
    code, porcelain = run_cmd(["git", "status", "--porcelain"])
    if code == 0:
        lines = [l for l in porcelain.split("\n") if l.strip()]
        status["uncommitted"] = len(lines)
        status["staged"] = sum(1 for l in lines if l[0] != ' ' and l[0] != '?')
        status["untracked"] = sum(1 for l in lines if l.startswith('??'))

    # Check if ahead/behind remote
    code, ahead_behind = run_cmd(["git", "rev-list", "--left-right", "--count", "@{u}...HEAD"])
    if code == 0:
        parts = ahead_behind.split()
        if len(parts) == 2:
            status["behind"] = int(parts[0])
            status["ahead"] = int(parts[1])

    # Get last commit info
    code, last_commit = run_cmd(["git", "log", "-1", "--format=%h %s", "--date=relative"])
    if code == 0:
        status["last_commit"] = last_commit[:60]

    return status


def check_project_context() -> list[str]:
    """Check for project-specific context files."""
    context_files = []
    cwd = os.getcwd()

    # Check for CLAUDE.md or .claude/settings.json
    if os.path.exists(os.path.join(cwd, "CLAUDE.md")):
        context_files.append("CLAUDE.md (project instructions)")

    if os.path.exists(os.path.join(cwd, ".claude", "settings.json")):
        context_files.append(".claude/settings.json (project hooks)")

    # Check for worktrees
    code, worktrees = run_cmd(["git", "worktree", "list", "--porcelain"])
    if code == 0:
        worktree_count = worktrees.count("worktree ") - 1  # Exclude main
        if worktree_count > 0:
            context_files.append(f"{worktree_count} active worktree(s)")

    # Check for TODO/FIXME in recent commits
    code, todos = run_cmd(["git", "log", "-5", "--format=%s", "--grep=TODO\\|FIXME\\|WIP"])
    if code == 0 and todos:
        context_files.append("Recent WIP/TODO commits detected")

    return context_files


def check_environment() -> dict:
    """Check development environment status."""
    env = {}

    # Check tmux
    if os.environ.get("TMUX"):
        code, session = run_cmd(["tmux", "display-message", "-p", "#S"])
        env["tmux"] = session if code == 0 else "active"

    # Check nix shell
    if os.environ.get("IN_NIX_SHELL"):
        env["nix_shell"] = os.environ.get("name", "active")

    # Check direnv
    if os.environ.get("DIRENV_DIR"):
        env["direnv"] = "active"

    # Check virtual environment
    if os.environ.get("VIRTUAL_ENV"):
        env["venv"] = os.path.basename(os.environ["VIRTUAL_ENV"])

    return env


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    # Only run on SessionStart
    hook_event = data.get("hook_event_name", "")
    if hook_event != "SessionStart":
        sys.exit(0)

    sections = []

    # Git status
    git = get_git_status()
    if git.get("is_repo"):
        git_lines = []
        if git.get("branch"):
            git_lines.append(f"Branch: {git['branch']}")
        if git.get("ahead", 0) > 0:
            git_lines.append(f"Ahead by {git['ahead']} commit(s)")
        if git.get("behind", 0) > 0:
            git_lines.append(f"Behind by {git['behind']} commit(s)")
        if git.get("uncommitted", 0) > 0:
            git_lines.append(f"Uncommitted: {git['uncommitted']} file(s)")
        if git.get("last_commit"):
            git_lines.append(f"Last: {git['last_commit']}")
        if git_lines:
            sections.append("Git: " + " | ".join(git_lines))

    # Environment
    env = check_environment()
    if env:
        env_items = [f"{k}: {v}" for k, v in env.items()]
        sections.append("Env: " + " | ".join(env_items))

    # Project context
    context = check_project_context()
    if context:
        sections.append("Context: " + ", ".join(context))

    # Time-based reminders
    hour = datetime.now().hour
    if hour >= 17:
        sections.append("Note: After hours - avoid risky deployments")
    elif hour < 9:
        sections.append("Note: Early hours - consider async work patterns")

    if sections:
        output = {
            "continue": True,
            "systemMessage": "SESSION CONTEXT:\n" + "\n".join(sections)
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
