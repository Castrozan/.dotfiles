import os
import subprocess


def run_wezterm_cli(socket_path, arguments):
    environment = dict(os.environ)
    environment["WEZTERM_UNIX_SOCKET"] = str(socket_path)
    return subprocess.run(
        ["wezterm", "cli", "--no-auto-start", *arguments],
        env=environment,
        capture_output=True,
        text=True,
    )


def spawn_new_window(socket_path):
    result = run_wezterm_cli(socket_path, ["spawn", "--new-window"])
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def close_window_by_pane(socket_path, pane_id):
    result = run_wezterm_cli(socket_path, ["kill-pane", "--pane-id", pane_id])
    return result.returncode == 0
