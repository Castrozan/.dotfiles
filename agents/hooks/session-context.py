#!/usr/bin/env python3

import json
import os
import platform
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict


def run_command_with_timeout(args: list[str], timeout: int = 5) -> tuple[int, str]:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 1, ""


def get_git_repository_status() -> Dict[str, Any]:
    code, _ = run_command_with_timeout(["git", "rev-parse", "--is-inside-work-tree"])
    if code != 0:
        return {"is_repo": False}

    status: dict[str, Any] = {"is_repo": True}

    code, branch = run_command_with_timeout(["git", "branch", "--show-current"])
    if code == 0:
        status["branch"] = branch

    code, porcelain_output = run_command_with_timeout(["git", "status", "--porcelain"])
    if code == 0:
        changed_file_lines = [
            line for line in porcelain_output.split("\n") if line.strip()
        ]
        status["uncommitted"] = len(changed_file_lines)
        status["staged"] = sum(
            1 for line in changed_file_lines if line[0] != " " and line[0] != "?"
        )
        status["untracked"] = sum(
            1 for line in changed_file_lines if line.startswith("??")
        )

    code, ahead_behind_output = run_command_with_timeout(
        ["git", "rev-list", "--left-right", "--count", "@{u}...HEAD"]
    )
    if code == 0:
        parts = ahead_behind_output.split()
        if len(parts) == 2:
            status["behind"] = int(parts[0])
            status["ahead"] = int(parts[1])

    code, last_commit_summary = run_command_with_timeout(
        ["git", "log", "-1", "--format=%h %s", "--date=relative"]
    )
    if code == 0:
        status["last_commit"] = last_commit_summary[:60]

    return status


def find_project_context_files() -> list[str]:
    context_files = []
    cwd = os.getcwd()

    if os.path.exists(os.path.join(cwd, "CLAUDE.md")):
        context_files.append("CLAUDE.md (project instructions)")

    if os.path.exists(os.path.join(cwd, ".claude", "settings.json")):
        context_files.append(".claude/settings.json (project hooks)")

    code, worktree_list_output = run_command_with_timeout(
        ["git", "worktree", "list", "--porcelain"]
    )
    if code == 0:
        active_worktree_count = worktree_list_output.count("worktree ") - 1
        if active_worktree_count > 0:
            context_files.append(f"{active_worktree_count} active worktree(s)")

    code, wip_todo_commits = run_command_with_timeout(
        ["git", "log", "-5", "--format=%s", "--grep=TODO\\|FIXME\\|WIP"]
    )
    if code == 0 and wip_todo_commits:
        context_files.append("Recent WIP/TODO commits detected")

    return context_files


def get_operating_system_info() -> Dict[str, str]:
    info = {}

    info["user"] = os.environ.get("USER", "unknown")

    system_name = platform.system()
    if system_name == "Darwin":
        macos_version = platform.mac_ver()[0]
        info["os"] = f"macOS {macos_version}" if macos_version else "macOS"
    else:
        try:
            release = platform.freedesktop_os_release()
            info["os"] = release.get("PRETTY_NAME", release.get("NAME", "unknown"))
        except (OSError, AttributeError):
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release") as f:
                    for os_release_line in f:
                        if os_release_line.startswith("PRETTY_NAME="):
                            info["os"] = (
                                os_release_line.split("=", 1)[1].strip().strip('"')
                            )
                            break
                        elif os_release_line.startswith("NAME=") and "os" not in info:
                            info["os"] = (
                                os_release_line.split("=", 1)[1].strip().strip('"')
                            )

    return info


def extract_vscode_project_name_from_title(window_title: str) -> str:
    suffix = " - Visual Studio Code"
    if not window_title.endswith(suffix):
        return window_title[:40]
    without_suffix = window_title[: -len(suffix)]
    parts = without_suffix.rsplit(" - ", 1)
    return parts[-1] if len(parts) > 1 else parts[0]


def summarize_workspace_windows(clients: list[dict], workspace_id: int) -> list[str]:
    workspace_clients = [
        client
        for client in clients
        if client.get("workspace", {}).get("id") == workspace_id
    ]

    terminal_classes = {"org.wezfurlong.wezterm", "kitty", "Alacritty", "foot"}
    vscode_classes = {"code", "code-url-handler", "Code"}
    browser_classes = {"brave-browser", "chrome-global", "firefox", "chromium-browser"}

    summaries = []
    terminal_count = 0

    for client in workspace_clients:
        window_class = client.get("class", "")
        window_title = client.get("title", "")

        if window_class in terminal_classes:
            terminal_count += 1
        elif window_class in vscode_classes:
            project_name = extract_vscode_project_name_from_title(window_title)
            summaries.append(f"code: {project_name}")
        elif window_class in browser_classes:
            short_class = window_class.split("-")[0]
            short_title = window_title[:50] if window_title else "untitled"
            summaries.append(f"{short_class}: {short_title}")
        elif window_class:
            summaries.append(window_class)

    if terminal_count == 1:
        summaries.append("wezterm")
    elif terminal_count > 1:
        summaries.append(f"wezterm (x{terminal_count})")

    return summaries


def detect_hyprland_workspace_context() -> dict:
    code, workspace_json = run_command_with_timeout(
        ["hyprctl", "activeworkspace", "-j"]
    )
    if code != 0 or not workspace_json:
        return {}

    try:
        workspace = json.loads(workspace_json)
    except json.JSONDecodeError:
        return {}

    workspace_id = workspace.get("id")
    if workspace_id is None:
        return {}

    context = {"id": workspace_id, "monitor": workspace.get("monitor", "")}

    code, clients_json = run_command_with_timeout(["hyprctl", "clients", "-j"])
    if code != 0 or not clients_json:
        return context

    try:
        clients = json.loads(clients_json)
    except json.JSONDecodeError:
        return context

    context["windows"] = summarize_workspace_windows(clients, workspace_id)
    return context


def format_hyprland_workspace_section(context: dict) -> str:
    header = f"#{context['id']}"
    if context.get("monitor"):
        header += f" on {context['monitor']}"

    windows = context.get("windows", [])
    if windows:
        return f"Workspace: {header} | " + ", ".join(windows)
    return f"Workspace: {header}"


def detect_active_development_environment() -> dict:
    environment = {}

    if os.environ.get("TMUX"):
        code, session_name = run_command_with_timeout(
            ["tmux", "display-message", "-p", "#S"]
        )
        environment["tmux"] = session_name if code == 0 else "active"

    if os.environ.get("IN_NIX_SHELL"):
        environment["nix_shell"] = os.environ.get("name", "active")

    if os.environ.get("DIRENV_DIR"):
        environment["direnv"] = "active"

    if os.environ.get("VIRTUAL_ENV"):
        environment["venv"] = os.path.basename(os.environ["VIRTUAL_ENV"])

    return environment


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    hook_event_name = data.get("hook_event_name", "")
    if hook_event_name != "SessionStart":
        sys.exit(0)

    sections = []

    git_status = get_git_repository_status()
    if git_status.get("is_repo"):
        git_summary_parts = []
        if git_status.get("branch"):
            git_summary_parts.append(f"Branch: {git_status['branch']}")
        if git_status.get("ahead", 0) > 0:
            git_summary_parts.append(f"Ahead by {git_status['ahead']} commit(s)")
        if git_status.get("behind", 0) > 0:
            git_summary_parts.append(f"Behind by {git_status['behind']} commit(s)")
        if git_status.get("uncommitted", 0) > 0:
            git_summary_parts.append(
                f"Uncommitted: {git_status['uncommitted']} file(s)"
            )
        if git_status.get("last_commit"):
            git_summary_parts.append(f"Last: {git_status['last_commit']}")
        if git_summary_parts:
            sections.append("Git: " + " | ".join(git_summary_parts))

    active_environment = detect_active_development_environment()
    if active_environment:
        environment_items = [f"{k}: {v}" for k, v in active_environment.items()]
        sections.append("Env: " + " | ".join(environment_items))

    hyprland_workspace = detect_hyprland_workspace_context()
    if hyprland_workspace:
        sections.append(format_hyprland_workspace_section(hyprland_workspace))

    project_context = find_project_context_files()
    if project_context:
        sections.append("Context: " + ", ".join(project_context))

    system_info = get_operating_system_info()
    system_info_parts = []
    if system_info.get("user"):
        system_info_parts.append(f"User: {system_info['user']}")
    if system_info.get("os"):
        system_info_parts.append(f"OS: {system_info['os']}")
    if system_info_parts:
        sections.append(" | ".join(system_info_parts))

    now = datetime.now()
    sections.append(f"Date: {now.strftime('%Y-%m-%d %H:%M')} ({now.strftime('%A')})")
    if now.hour >= 18:
        sections.append("Note: After hours - avoid risky deployments")

    if sections:
        output = {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": "SESSION CONTEXT:\n" + "\n".join(sections),
            },
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
