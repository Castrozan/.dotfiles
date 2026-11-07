from hyprland_ipc import get_all_monitors, run_hyprctl
from monitor_configuration import (
    DisplayMode,
    apply_display_mode,
    hold_reconcile_lock,
    is_internal_monitor_name,
    read_connected_monitors,
    send_monitor_notification,
    write_display_mode,
)


def recenter_cursor_on_internal_monitor() -> None:
    for monitor in get_all_monitors(include_disabled=False):
        if is_internal_monitor_name(monitor.get("name", "")):
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


def force_builtin_only() -> bool:
    with hold_reconcile_lock():
        monitors = read_connected_monitors()
        if not monitors.internal:
            return False
        write_display_mode(DisplayMode.INTERNAL)
        apply_display_mode(DisplayMode.INTERNAL, monitors)
        return True


def main() -> None:
    if not force_builtin_only():
        send_monitor_notification("No internal monitor found")
        return
    recenter_cursor_on_internal_monitor()
    send_monitor_notification("Built-in only")


if __name__ == "__main__":
    main()
