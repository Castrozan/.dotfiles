"""Detect and summarize the current Hyprland workspace + windows for session context."""

from __future__ import annotations

import json

from session_context_command_runner import run_cmd


def run_command_with_timeout(args: list[str], timeout: int = 5) -> tuple[int, str]:
    return run_cmd(args, timeout)


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
    if not context:
        return ""
    header = f"#{context['id']}"
    if context.get("monitor"):
        header += f" on {context['monitor']}"

    windows = context.get("windows", [])
    if windows:
        return f"Workspace: {header} | " + ", ".join(windows)
    return f"Workspace: {header}"
