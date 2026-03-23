import os
import socket
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from hyprland_ipc import (
    get_active_window,
    get_active_workspace_id,
    get_all_clients,
    get_all_workspaces,
    run_hyprctl,
    run_hyprctl_batch,
)

RECONNECT_INITIAL_DELAY_SECONDS = 1
RECONNECT_MAX_DELAY_SECONDS = 30
OPENED_WINDOW_WORKSPACE_LOOKUP_ATTEMPTS = 5
OPENED_WINDOW_WORKSPACE_LOOKUP_DELAY_SECONDS = 0.03
OFFSCREEN_POSITION = "-9999 -9999"


@dataclass
class DaemonState:
    maximized_workspace_ids: set[int] = field(default_factory=set)
    current_focused_address: str = ""
    previous_focused_address: str = ""


def get_active_window_fullscreen_state() -> int:
    window = get_active_window()
    if not window:
        return 0
    return window.get("fullscreen", 0)


def workspace_has_fullscreen_window(workspace_id: int) -> bool:
    for workspace in get_all_workspaces():
        if workspace.get("id") == workspace_id:
            return workspace.get("hasfullscreen", False)
    return False


def find_window_workspace_id_by_address(window_address: str) -> int | None:
    for client in get_all_clients():
        if client.get("address") == window_address:
            return client.get("workspace", {}).get("id")
    return None


def find_opened_window_workspace_id(window_address: str) -> int | None:
    for _ in range(OPENED_WINDOW_WORKSPACE_LOOKUP_ATTEMPTS):
        workspace_id = find_window_workspace_id_by_address(window_address)
        if workspace_id is not None:
            return workspace_id
        time.sleep(OPENED_WINDOW_WORKSPACE_LOOKUP_DELAY_SECONDS)
    return None


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


def remaximize_active_workspace_if_needed(state: DaemonState) -> None:
    workspace_id = get_active_workspace_id()
    if workspace_id is None or workspace_id not in state.maximized_workspace_ids:
        return

    if get_active_window_fullscreen_state() == 1:
        return

    tiled_count = sum(
        1
        for c in get_all_clients()
        if c.get("workspace", {}).get("id") == workspace_id
        and not c.get("floating", False)
    )

    if tiled_count > 0:
        run_hyprctl("dispatch", "fullscreen 1 set")
    else:
        state.maximized_workspace_ids.discard(workspace_id)


def force_remaximize_active_workspace(state: DaemonState) -> None:
    workspace_id = get_active_workspace_id()
    if workspace_id is None or workspace_id not in state.maximized_workspace_ids:
        return

    tiled_count = sum(
        1
        for c in get_all_clients()
        if c.get("workspace", {}).get("id") == workspace_id
        and not c.get("floating", False)
    )

    if tiled_count > 0:
        run_hyprctl_batch(
            "dispatch fullscreen 1 unset ; dispatch fullscreen 1 set"
        )
    else:
        state.maximized_workspace_ids.discard(workspace_id)


def handle_active_window_changed_event(state: DaemonState, raw_address: str) -> None:
    window_address = f"0x{raw_address}"
    if window_address != state.current_focused_address:
        state.previous_focused_address = state.current_focused_address
        state.current_focused_address = window_address
    restore_floating_window_to_center(window_address)
    move_floating_windows_offscreen(window_address)


def handle_fullscreen_event(state: DaemonState, fullscreen_state_str: str) -> None:
    if fullscreen_state_str == "1":
        workspace_id = get_active_workspace_id()
        if workspace_id is not None:
            state.maximized_workspace_ids.add(workspace_id)


def ensure_remaining_tiled_windows_on_active_workspace_are_grouped() -> None:
    subprocess.run(["hypr-ensure-workspace-grouped"], capture_output=True)


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

    time.sleep(0.03)
    force_remaximize_active_workspace(state)
    ensure_remaining_tiled_windows_on_active_workspace_are_grouped()


def handle_workspace_changed_event(state: DaemonState, _data: str) -> None:
    time.sleep(0.05)
    remaximize_active_workspace_if_needed(state)


def is_window_floating(window_address: str) -> bool:
    for client in get_all_clients():
        if client.get("address") == window_address:
            return client.get("floating", False)
    return False


def handle_open_window_event(state: DaemonState, event_data: str) -> None:
    raw_address = event_data.split(",")[0]
    window_address = f"0x{raw_address}"

    workspace_id = find_opened_window_workspace_id(window_address)
    if workspace_id is None or workspace_id not in state.maximized_workspace_ids:
        return

    active_workspace_id = get_active_workspace_id()
    if workspace_id != active_workspace_id:
        return

    if is_window_floating(window_address):
        return

    run_hyprctl_batch(
        f"dispatch focuswindow address:{window_address} ; dispatch fullscreen 1 set"
    )


EVENT_HANDLERS = {
    "activewindowv2": handle_active_window_changed_event,
    "fullscreen": handle_fullscreen_event,
    "closewindow": handle_close_window_event,
    "openwindow": handle_open_window_event,
    "workspace": handle_workspace_changed_event,
}


def initialize_maximized_workspace_tracking(state: DaemonState) -> None:
    state.maximized_workspace_ids.clear()
    for workspace in get_all_workspaces():
        if workspace.get("hasfullscreen", False):
            state.maximized_workspace_ids.add(workspace["id"])


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
        initialize_maximized_workspace_tracking(state)
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
