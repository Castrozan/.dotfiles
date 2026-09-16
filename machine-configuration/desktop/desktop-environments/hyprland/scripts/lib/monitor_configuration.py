import os
import re
import subprocess
import time
from pathlib import Path

from hyprland_ipc import run_hyprctl

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


def write_toggle_lock() -> None:
    TOGGLE_LOCK_FILE.write_text(str(time.time()))


def write_override_and_reload(content: str) -> None:
    write_toggle_lock()
    OVERRIDE_FILE.write_text(content)
    run_hyprctl("reload")


def send_monitor_notification(message: str) -> None:
    subprocess.run(
        ["notify-send", "-t", "2000", "Monitor", message],
        capture_output=True,
    )
