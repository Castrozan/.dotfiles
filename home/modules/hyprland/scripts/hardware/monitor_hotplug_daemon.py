import os
import socket
import time
from pathlib import Path

from hyprland_ipc import (
    get_all_monitors,
    migrate_workspaces_from_disabled_monitors,
    run_hyprctl,
)

OVERRIDE_FILE = Path.home() / ".cache" / "hypr-monitors-override.conf"
TOGGLE_LOCK_FILE = Path.home() / ".cache" / "hypr-monitors-toggle.lock"
TOGGLE_LOCK_TIMEOUT_SECONDS = 5
RECONNECT_INITIAL_DELAY_SECONDS = 1
RECONNECT_MAX_DELAY_SECONDS = 30


def write_override_and_reload(content: str) -> None:
    OVERRIDE_FILE.write_text(content)
    run_hyprctl("reload")


def has_external_monitor_connected() -> bool:
    monitors = get_all_monitors(include_disabled=True)
    if not monitors:
        return False
    return any(
        not monitor_config.get("name", "").startswith("eDP")
        for monitor_config in monitors
    )


def is_manual_toggle_in_progress() -> bool:
    if not TOGGLE_LOCK_FILE.exists():
        return False
    try:
        lock_timestamp = float(TOGGLE_LOCK_FILE.read_text())
        return (time.time() - lock_timestamp) < TOGGLE_LOCK_TIMEOUT_SECONDS
    except (ValueError, OSError):
        return False


def handle_monitor_removed(monitor_name: str) -> None:
    if monitor_name.startswith("eDP"):
        return
    if is_manual_toggle_in_progress():
        return
    write_override_and_reload("monitor = eDP-1, preferred, auto, 1")
    migrate_workspaces_from_disabled_monitors()


def handle_monitor_added(monitor_name: str) -> None:
    if monitor_name.startswith("eDP"):
        return
    if is_manual_toggle_in_progress():
        return
    write_override_and_reload("")
    migrate_workspaces_from_disabled_monitors()


def check_initial_state() -> None:
    if not has_external_monitor_connected():
        write_override_and_reload("monitor = eDP-1, preferred, auto, 1")


def build_event_socket_path() -> str:
    hyprland_instance_signature = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
    xdg_runtime_dir = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
    return f"{xdg_runtime_dir}/hypr/{hyprland_instance_signature}/.socket2.sock"


EVENT_HANDLERS = {
    "monitorremoved": handle_monitor_removed,
    "monitoradded": handle_monitor_added,
}


def read_and_dispatch_events(event_socket_path: str) -> None:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(event_socket_path)
        with sock.makefile("r") as stream:
            for line in stream:
                line = line.strip()
                if ">>" not in line:
                    continue
                event, _, data = line.partition(">>")
                handler = EVENT_HANDLERS.get(event)
                if handler:
                    handler(data)
    finally:
        sock.close()


def main() -> None:
    event_socket_path = build_event_socket_path()
    reconnect_delay_seconds = RECONNECT_INITIAL_DELAY_SECONDS

    check_initial_state()

    while True:
        try:
            read_and_dispatch_events(event_socket_path)
            reconnect_delay_seconds = RECONNECT_INITIAL_DELAY_SECONDS
        except (ConnectionError, OSError):
            pass

        while not Path(event_socket_path).is_socket():
            time.sleep(reconnect_delay_seconds)

        reconnect_delay_seconds = min(
            reconnect_delay_seconds * 2, RECONNECT_MAX_DELAY_SECONDS
        )


if __name__ == "__main__":
    main()
