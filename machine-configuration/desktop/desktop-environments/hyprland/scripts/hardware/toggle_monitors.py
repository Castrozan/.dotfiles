from pathlib import Path

from monitor_configuration import (
    DisplayMode,
    apply_display_mode,
    hold_reconcile_lock,
    read_connected_monitors,
    read_display_mode,
    send_monitor_notification,
    write_display_mode,
)

LID_STATE_FILE = Path("/proc/acpi/button/lid/LID0/state")

DISPLAY_MODE_LABELS = {
    DisplayMode.EXTERNAL: "External only",
    DisplayMode.EXTENDED: "Extended",
    DisplayMode.INTERNAL: "Built-in only",
}

LID_OPEN_TRANSITIONS = {
    DisplayMode.EXTERNAL: DisplayMode.EXTENDED,
    DisplayMode.EXTENDED: DisplayMode.INTERNAL,
    DisplayMode.INTERNAL: DisplayMode.EXTERNAL,
}


def laptop_lid_is_closed() -> bool:
    if not LID_STATE_FILE.exists():
        return False
    return "closed" in LID_STATE_FILE.read_text().lower()


def determine_next_mode(current_mode: DisplayMode, lid_closed: bool) -> DisplayMode:
    if lid_closed:
        if current_mode is DisplayMode.EXTENDED:
            return DisplayMode.EXTERNAL
        return DisplayMode.EXTENDED
    return LID_OPEN_TRANSITIONS[current_mode]


def toggle_display_mode() -> str:
    with hold_reconcile_lock():
        monitors = read_connected_monitors()
        if not monitors.internal:
            return "No internal monitor found"
        current_mode = read_display_mode()
        if not monitors.externals:
            if apply_display_mode(current_mode, monitors):
                return DISPLAY_MODE_LABELS[DisplayMode.INTERNAL]
            return "No external monitor connected"
        next_mode = determine_next_mode(current_mode, laptop_lid_is_closed())
        write_display_mode(next_mode)
        apply_display_mode(next_mode, monitors)
        return DISPLAY_MODE_LABELS[next_mode]


def main() -> None:
    send_monitor_notification(toggle_display_mode())


if __name__ == "__main__":
    main()
