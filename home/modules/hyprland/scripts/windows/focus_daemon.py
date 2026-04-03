import os
import socket
import time
from dataclasses import dataclass
from pathlib import Path

from hyprland_ipc import (
    get_active_window,
    get_all_clients,
    run_hyprctl,
)

RECONNECT_INITIAL_DELAY_SECONDS = 1
RECONNECT_MAX_DELAY_SECONDS = 30
OFFSCREEN_POSITION = "-9999 -9999"


@dataclass
class DaemonState:
    current_focused_address: str = ""
    previous_focused_address: str = ""


def find_focused_window_properties(
    focused_address: str,
) -> tuple[bool, int] | None:
    for client in get_all_clients():
        if client.get("address") == focused_address:
            is_floating = client.get("floating", False)
            workspace_id = client.get("workspace", {}).get("id")
            if workspace_id is not None:
                return (is_floating, workspace_id)
    return None


def collect_floating_window_addresses_on_workspace(
    workspace_id: int, exclude_address: str
) -> list[str]:
    return [
        client["address"]
        for client in get_all_clients()
        if client.get("workspace", {}).get("id") == workspace_id
        and client.get("floating") is True
        and client.get("pinned") is not True
        and client.get("address") != exclude_address
    ]


def move_floating_windows_offscreen(focused_address: str) -> None:
    properties = find_focused_window_properties(focused_address)
    if not properties:
        return

    is_floating, workspace_id = properties
    if is_floating:
        return

    for address in collect_floating_window_addresses_on_workspace(
        workspace_id, focused_address
    ):
        run_hyprctl(
            "dispatch",
            f"movewindowpixel exact {OFFSCREEN_POSITION},address:{address}",
        )


def restore_floating_window_to_center(window_address: str) -> None:
    for client in get_all_clients():
        if client.get("address") == window_address:
            if client.get("floating") is True:
                run_hyprctl("dispatch", f"centerwindow address:{window_address}")
            return


def handle_active_window_changed_event(state: DaemonState, raw_address: str) -> None:
    window_address = f"0x{raw_address}"
    if window_address != state.current_focused_address:
        state.previous_focused_address = state.current_focused_address
        state.current_focused_address = window_address
    restore_floating_window_to_center(window_address)
    move_floating_windows_offscreen(window_address)


def handle_close_window_event(state: DaemonState, raw_address: str) -> None:
    closed_address = f"0x{raw_address}"

    if (
        closed_address == state.current_focused_address
        and state.previous_focused_address
    ):
        run_hyprctl(
            "dispatch",
            f"focuswindow address:{state.previous_focused_address}",
        )
        state.current_focused_address = state.previous_focused_address
        state.previous_focused_address = ""
    elif closed_address == state.previous_focused_address:
        state.previous_focused_address = ""


EVENT_HANDLERS = {
    "activewindowv2": handle_active_window_changed_event,
    "closewindow": handle_close_window_event,
}


def initialize_focused_window_tracking(state: DaemonState) -> None:
    window = get_active_window()
    state.current_focused_address = window.get("address", "") if window else ""
    state.previous_focused_address = ""


def read_and_dispatch_hyprland_events(
    state: DaemonState, event_socket_path: str
) -> None:
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
                    handler(state, data)
    finally:
        sock.close()


def build_event_socket_path() -> str:
    hyprland_instance_signature = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
    xdg_runtime_dir = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
    return f"{xdg_runtime_dir}/hypr/{hyprland_instance_signature}/.socket2.sock"


def connect_and_process_events_with_reconnect() -> None:
    event_socket_path = build_event_socket_path()
    state = DaemonState()
    reconnect_delay_seconds = RECONNECT_INITIAL_DELAY_SECONDS

    while True:
        initialize_focused_window_tracking(state)

        try:
            read_and_dispatch_hyprland_events(state, event_socket_path)
            reconnect_delay_seconds = RECONNECT_INITIAL_DELAY_SECONDS
        except (ConnectionError, OSError):
            pass

        while not Path(event_socket_path).is_socket():
            time.sleep(reconnect_delay_seconds)

        reconnect_delay_seconds = min(
            reconnect_delay_seconds * 2, RECONNECT_MAX_DELAY_SECONDS
        )


def main() -> None:
    connect_and_process_events_with_reconnect()


if __name__ == "__main__":
    main()
