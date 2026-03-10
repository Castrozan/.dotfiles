import json
import subprocess


def run_hyprctl(*args: str) -> str:
    result = subprocess.run(
        ["hyprctl", *args],
        capture_output=True,
        text=True,
    )
    return result.stdout


def run_hyprctl_json(*args: str) -> dict | list | None:
    output = run_hyprctl(*args, "-j")
    if not output.strip():
        return None
    return json.loads(output)


def run_hyprctl_batch(commands: str) -> None:
    subprocess.run(["hyprctl", "--batch", commands], capture_output=True)


def get_active_window() -> dict | None:
    return run_hyprctl_json("activewindow")


def get_active_workspace_id() -> int | None:
    window = get_active_window()
    if not window:
        return None
    return window.get("workspace", {}).get("id")


def get_all_clients() -> list[dict]:
    return run_hyprctl_json("clients") or []


def get_all_workspaces() -> list[dict]:
    return run_hyprctl_json("workspaces") or []


def get_focused_monitor() -> dict | None:
    monitors = run_hyprctl_json("monitors")
    if not monitors:
        return None
    for monitor in monitors:
        if monitor.get("focused"):
            return monitor
    return None
