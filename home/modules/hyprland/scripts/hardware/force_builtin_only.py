import os
import re
import subprocess
import time
from pathlib import Path

from hyprland_ipc import (
    get_all_monitors,
    migrate_workspaces_from_disabled_monitors,
    run_hyprctl,
)

MONITORS_CONF = (
    Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    / "hypr-host"
    / "monitors.conf"
)
OVERRIDE_FILE = Path.home() / ".cache" / "hypr-monitors-override.conf"
TOGGLE_LOCK_FILE = Path.home() / ".cache" / "hypr-monitors-toggle.lock"


def find_enabled_config_line_for_monitor(monitor_name: str) -> str:
    if not MONITORS_CONF.exists():
        return f"{monitor_name}, preferred, auto, 1"
    for line in MONITORS_CONF.read_text().splitlines():
        if re.match(rf"\s*monitor\s*=\s*{re.escape(monitor_name)}\s*,", line):
            if "disable" not in line:
                return re.sub(r"^\s*monitor\s*=\s*", "", line).strip()
    return f"{monitor_name}, preferred, auto, 1"


def find_internal_monitor_name(monitor_names: list[str]) -> str | None:
    for name in monitor_names:
        if name.startswith("eDP"):
            return name
    return None


def find_external_monitor_names(monitor_names: list[str]) -> list[str]:
    return [name for name in monitor_names if not name.startswith("eDP")]


def build_override_content_for_builtin_only(
    internal_monitor: str, external_monitors: list[str]
) -> str:
    internal_config_line = find_enabled_config_line_for_monitor(internal_monitor)
    override_lines = [f"monitor = {internal_config_line}"]
    for external_monitor in external_monitors:
        override_lines.append(f"monitor = {external_monitor}, disable")
    override_lines.append("monitor = , disable")
    return "\n".join(override_lines) + "\n"


def write_toggle_lock() -> None:
    TOGGLE_LOCK_FILE.write_text(str(time.time()))


def write_override_and_reload(content: str) -> None:
    write_toggle_lock()
    OVERRIDE_FILE.write_text(content)
    run_hyprctl("reload")


def recenter_cursor_on_internal_monitor() -> None:
    for monitor in get_all_monitors(include_disabled=False):
        if monitor.get("name", "").startswith("eDP"):
            width = monitor.get("width", 0)
            height = monitor.get("height", 0)
            x_position = monitor.get("x", 0)
            y_position = monitor.get("y", 0)
            if width and height:
                run_hyprctl(
                    "dispatch",
                    "movecursor",
                    str(x_position + width // 2),
                    str(y_position + height // 2),
                )
            return


def send_notification(message: str) -> None:
    subprocess.run(
        ["notify-send", "-t", "2000", "Monitor", message],
        capture_output=True,
    )


def main() -> None:
    all_monitors = get_all_monitors(include_disabled=True)
    all_monitor_names = [monitor.get("name", "") for monitor in all_monitors]

    internal_monitor = find_internal_monitor_name(all_monitor_names)
    if not internal_monitor:
        send_notification("No internal monitor found")
        return

    external_monitors = find_external_monitor_names(all_monitor_names)
    override_content = build_override_content_for_builtin_only(
        internal_monitor, external_monitors
    )
    write_override_and_reload(override_content)
    migrate_workspaces_from_disabled_monitors()
    recenter_cursor_on_internal_monitor()
    send_notification("Built-in only")


if __name__ == "__main__":
    main()
