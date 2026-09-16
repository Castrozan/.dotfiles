import re
import subprocess
from pathlib import Path

THEME_HYPRLAND_CONF = (
    Path.home() / ".config" / "hypr-theme" / "current" / "theme" / "hyprland.conf"
)


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
