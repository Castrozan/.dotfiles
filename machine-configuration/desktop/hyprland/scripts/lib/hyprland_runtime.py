import os
import subprocess
from pathlib import Path


def build_event_socket_path() -> str:
    hyprland_instance_signature = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
    xdg_runtime_dir = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
    return f"{xdg_runtime_dir}/hypr/{hyprland_instance_signature}/.socket2.sock"


def is_hyprctl_connected() -> bool:
    result = subprocess.run(
        ["hyprctl", "monitors"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def find_live_hyprland_socket() -> bool:
    uid = os.getuid()
    hypr_dir = Path(f"/run/user/{uid}/hypr")
    if not hypr_dir.is_dir():
        return False

    for candidate in hypr_dir.iterdir():
        if not candidate.is_dir():
            continue
        signature = candidate.name
        env = os.environ.copy()
        env["HYPRLAND_INSTANCE_SIGNATURE"] = signature
        result = subprocess.run(
            ["hyprctl", "monitors"],
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode == 0:
            os.environ["HYPRLAND_INSTANCE_SIGNATURE"] = signature
            return True
    return False


def ensure_hyprctl_connected() -> bool:
    if is_hyprctl_connected():
        return True
    return find_live_hyprland_socket()
