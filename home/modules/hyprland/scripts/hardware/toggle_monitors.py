import os
import re
import subprocess
from pathlib import Path

from hyprland_ipc import get_all_monitors, run_hyprctl

MONITORS_CONF = (
    Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    / "hypr-host"
    / "monitors.conf"
)
OVERRIDE_FILE = Path.home() / ".cache" / "hypr-monitors-override.conf"
LID_STATE_FILE = Path("/proc/acpi/button/lid/LID0/state")


def extract_monitor_names_from_config() -> list[str]:
    if not MONITORS_CONF.exists():
        return []
    names = set()
    for line in MONITORS_CONF.read_text().splitlines():
        match = re.match(r"\s*monitor\s*=\s*([^,]+)", line)
        if match:
            names.add(match.group(1).strip())
    return sorted(names)


def find_enabled_config_line_for_monitor(monitor_name: str) -> str:
    if not MONITORS_CONF.exists():
        return f"{monitor_name}, preferred, auto, 1"
    for line in MONITORS_CONF.read_text().splitlines():
        if re.match(rf"\s*monitor\s*=\s*{re.escape(monitor_name)}\s*,", line):
            if "disable" not in line:
                return re.sub(r"^\s*monitor\s*=\s*", "", line).strip()
    return f"{monitor_name}, preferred, auto, 1"


def laptop_lid_is_closed() -> bool:
    if not LID_STATE_FILE.exists():
        return False
    return "closed" in LID_STATE_FILE.read_text().lower()


def detect_current_mode(
    active_names: list[str],
    internal_monitor: str,
    external_monitor: str,
) -> str:
    has_internal = internal_monitor in active_names
    has_external = external_monitor in active_names
    if has_internal and has_external:
        return "extended"
    if has_external:
        return "external"
    return "internal"


def determine_next_mode_with_lid_closed(current_mode: str) -> tuple[str, str]:
    if current_mode == "extended":
        return "external", "External only"
    return "extended", "Extended"


def determine_next_mode_with_lid_open(current_mode: str) -> tuple[str, str]:
    mode_transitions = {
        "external": ("extended", "Extended"),
        "extended": ("internal", "Built-in only"),
        "internal": ("external", "External only"),
    }
    return mode_transitions.get(current_mode, ("external", "External only"))


def build_override_content_for_mode(
    mode: str, internal_monitor: str, external_monitor: str
) -> str:
    if mode == "external":
        return ""
    if mode == "extended":
        config = find_enabled_config_line_for_monitor(internal_monitor)
        return f"monitor = {config}"
    config = find_enabled_config_line_for_monitor(internal_monitor)
    return f"monitor = {config}\nmonitor = {external_monitor}, disable"


def write_override_and_reload(content: str) -> None:
    OVERRIDE_FILE.write_text(content)
    run_hyprctl("reload")


def send_notification(message: str) -> None:
    subprocess.run(
        ["notify-send", "-t", "2000", "Monitor", message],
        capture_output=True,
    )


def find_internal_monitor(all_monitor_names: list[str]) -> str | None:
    for name in all_monitor_names:
        if name.startswith("eDP"):
            return name
    config_names = extract_monitor_names_from_config()
    for name in config_names:
        if name.startswith("eDP"):
            return name
    return None


def find_external_monitor(all_monitor_names: list[str]) -> str | None:
    for name in all_monitor_names:
        if not name.startswith("eDP"):
            return name
    return None


def main() -> None:
    active_monitors = get_all_monitors()
    active_names = [m.get("name", "") for m in active_monitors]

    all_monitors = get_all_monitors(include_disabled=True)
    all_names = [m.get("name", "") for m in all_monitors]

    internal_monitor = find_internal_monitor(all_names)
    external_monitor = find_external_monitor(all_names)

    if not internal_monitor:
        send_notification("No internal monitor found")
        return

    if not external_monitor:
        if internal_monitor not in active_names:
            write_override_and_reload(
                f"monitor = {internal_monitor}, preferred, auto, 1"
            )
            send_notification("Built-in only")
        else:
            send_notification("No external monitor connected")
        return

    current_mode = detect_current_mode(active_names, internal_monitor, external_monitor)

    if laptop_lid_is_closed():
        next_mode, label = determine_next_mode_with_lid_closed(current_mode)
    else:
        next_mode, label = determine_next_mode_with_lid_open(current_mode)

    override_content = build_override_content_for_mode(
        next_mode, internal_monitor, external_monitor
    )
    write_override_and_reload(override_content)
    send_notification(label)


if __name__ == "__main__":
    main()
