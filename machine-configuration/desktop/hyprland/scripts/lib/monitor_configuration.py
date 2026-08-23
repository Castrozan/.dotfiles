import os
import re
import subprocess
from pathlib import Path

MONITORS_CONF = (
    Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    / "hypr-host"
    / "monitors.conf"
)


def find_enabled_config_line_for_monitor(monitor_name: str) -> str:
    if not MONITORS_CONF.exists():
        return f"{monitor_name}, preferred, auto, 1"
    for line in MONITORS_CONF.read_text().splitlines():
        if re.match(rf"\s*monitor\s*=\s*{re.escape(monitor_name)}\s*,", line):
            if "disable" not in line:
                return re.sub(r"^\s*monitor\s*=\s*", "", line).strip()
    return f"{monitor_name}, preferred, auto, 1"


def send_monitor_notification(message: str) -> None:
    subprocess.run(
        ["notify-send", "-t", "2000", "Monitor", message],
        capture_output=True,
    )
