import os
import re
import subprocess
from pathlib import Path

THEME_HYPRLAND_CONF = (
    Path.home() / ".config" / "hypr-theme" / "current" / "theme" / "hyprland.conf"
)


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


def apply_theme_border_colors_from_config() -> None:
    if not THEME_HYPRLAND_CONF.is_file():
        return

    content = THEME_HYPRLAND_CONF.read_text()
    match = re.search(r"rgb\([^)]+\)", content)
    if not match:
        return

    color = match.group(0)
    subprocess.run(
        ["hyprctl", "keyword", "general:col.active_border", color],
        capture_output=True,
    )
    subprocess.run(
        ["hyprctl", "keyword", "group:col.border_active", color],
        capture_output=True,
    )


def main() -> None:
    if not ensure_hyprctl_connected():
        return
    apply_theme_border_colors_from_config()


if __name__ == "__main__":
    main()
