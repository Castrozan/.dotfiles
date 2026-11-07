import fcntl
import os
import re
import subprocess
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
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
DISPLAY_MODE_FILE = Path.home() / ".cache" / "hypr-monitors-mode"
RECONCILE_LOCK_FILE = Path.home() / ".cache" / "hypr-monitors.lock"
PLACEHOLDER_MONITOR_NAMES = frozenset({"", "FALLBACK"})
INTERNAL_PANEL_NAME_PATTERN = re.compile(r"^(eDP|LVDS|DSI)-")


class DisplayMode(StrEnum):
    EXTERNAL = "external"
    EXTENDED = "extended"
    INTERNAL = "internal"


@dataclass(frozen=True)
class ConnectedMonitors:
    internal: str | None
    externals: tuple[str, ...]


def is_internal_monitor_name(monitor_name: str) -> bool:
    return bool(INTERNAL_PANEL_NAME_PATTERN.match(monitor_name))


def extract_monitor_names_from_config() -> list[str]:
    if not MONITORS_CONF.exists():
        return []
    names = set()
    for line in MONITORS_CONF.read_text().splitlines():
        match = re.match(r"\s*monitor\s*=\s*([^,]+)", line)
        if match:
            names.add(match.group(1).strip())
    return sorted(names)


def classify_monitor_names(monitor_names: list[str]) -> ConnectedMonitors:
    real_names = [
        name for name in monitor_names if name not in PLACEHOLDER_MONITOR_NAMES
    ]
    internal_candidates = [
        name for name in real_names if is_internal_monitor_name(name)
    ] or [
        name
        for name in extract_monitor_names_from_config()
        if is_internal_monitor_name(name)
    ]
    return ConnectedMonitors(
        internal=internal_candidates[0] if internal_candidates else None,
        externals=tuple(
            name for name in real_names if not is_internal_monitor_name(name)
        ),
    )


def read_connected_monitors() -> ConnectedMonitors:
    return classify_monitor_names(
        [monitor.get("name", "") for monitor in get_all_monitors(include_disabled=True)]
    )


def find_enabled_config_line_for_monitor(monitor_name: str) -> str:
    if not MONITORS_CONF.exists():
        return f"{monitor_name}, preferred, auto, 1"
    for line in MONITORS_CONF.read_text().splitlines():
        if re.match(rf"\s*monitor\s*=\s*{re.escape(monitor_name)}\s*,", line):
            if "disable" not in line:
                return re.sub(r"^\s*monitor\s*=\s*", "", line).strip()
    return f"{monitor_name}, preferred, auto, 1"


def render_override(mode: DisplayMode, monitors: ConnectedMonitors) -> str:
    if not monitors.internal:
        return ""
    internal_line = (
        f"monitor = {find_enabled_config_line_for_monitor(monitors.internal)}"
    )
    if not monitors.externals or mode is DisplayMode.EXTENDED:
        return internal_line
    if mode is DisplayMode.EXTERNAL:
        return ""
    disabled_external_lines = [
        f"monitor = {external}, disable" for external in monitors.externals
    ]
    return "\n".join([internal_line, *disabled_external_lines, "monitor = , disable"])


def read_display_mode() -> DisplayMode:
    try:
        return DisplayMode(DISPLAY_MODE_FILE.read_text().strip())
    except (OSError, ValueError):
        return DisplayMode.EXTERNAL


def write_display_mode(mode: DisplayMode) -> None:
    DISPLAY_MODE_FILE.write_text(mode.value)


@contextmanager
def hold_reconcile_lock() -> Iterator[None]:
    with RECONCILE_LOCK_FILE.open("w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        yield


def apply_display_mode(mode: DisplayMode, monitors: ConnectedMonitors) -> bool:
    override_content = render_override(mode, monitors)
    if OVERRIDE_FILE.exists() and OVERRIDE_FILE.read_text() == override_content:
        return False
    OVERRIDE_FILE.write_text(override_content)
    run_hyprctl("reload")
    migrate_workspaces_from_disabled_monitors()
    return True


def reconcile_with_connected_monitors() -> None:
    with hold_reconcile_lock():
        apply_display_mode(read_display_mode(), read_connected_monitors())


def send_monitor_notification(message: str) -> None:
    subprocess.run(
        ["notify-send", "-t", "2000", "Monitor", message],
        capture_output=True,
    )
