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
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return None


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


def get_all_monitors(include_disabled: bool = False) -> list[dict]:
    if include_disabled:
        return run_hyprctl_json("monitors", "all") or []
    return run_hyprctl_json("monitors") or []


def get_focused_monitor() -> dict | None:
    for monitor in get_all_monitors():
        if monitor.get("focused"):
            return monitor
    return None
