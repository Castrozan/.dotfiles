import time

from hyprland_ipc import (
    get_all_clients,
    run_hyprctl,
    run_hyprctl_batch,
)

GROUP_MERGE_DELAY_SECONDS = 0.15
RETRY_DELAY_SECONDS = 0.3


def get_tiled_window_addresses_on_workspace(workspace_id: int) -> list[str]:
    return [
        client["address"]
        for client in get_all_clients()
        if client.get("workspace", {}).get("id") == workspace_id
        and not client.get("floating", False)
    ]


def all_tiled_windows_are_in_single_group_on_workspace(
    workspace_id: int,
) -> bool:
    tiled = [
        client_window
        for client_window in get_all_clients()
        if client_window.get("workspace", {}).get("id") == workspace_id
        and not client_window.get("floating", False)
    ]
    if not tiled:
        return False
    total = len(tiled)
    max_group = max(len(tiled_window.get("grouped", [])) for tiled_window in tiled)
    return max_group == total


def get_window_grouped_count(window_address: str) -> int:
    for client in get_all_clients():
        if client.get("address") == window_address:
            return len(client.get("grouped", []))
    return 0


def build_focus_command(address: str) -> str:
    return f"dispatch focuswindow address:{address}"


def build_merge_into_group_commands() -> str:
    return (
        "dispatch moveintogroup l;"
        " dispatch moveintogroup r;"
        " dispatch moveintogroup u;"
        " dispatch moveintogroup d"
    )


def ensure_first_window_starts_group(address: str) -> None:
    grouped_count = get_window_grouped_count(address)
    focus = build_focus_command(address)

    if grouped_count == 0:
        run_hyprctl_batch(
            f"{focus}; dispatch togglegroup; dispatch lockactivegroup unlock"
        )
    elif grouped_count == 1:
        run_hyprctl_batch(f"{focus}; dispatch lockactivegroup unlock")
    else:
        run_hyprctl_batch(
            f"{focus}; dispatch moveoutofgroup;"
            " dispatch togglegroup; dispatch lockactivegroup unlock"
        )


def dissolve_and_move_into_target_group(address: str) -> None:
    grouped_count = get_window_grouped_count(address)
    focus = build_focus_command(address)
    merge = build_merge_into_group_commands()

    if grouped_count == 1:
        run_hyprctl_batch(f"{focus}; dispatch togglegroup; {merge}")
    elif grouped_count == 0:
        run_hyprctl_batch(f"{focus}; {merge}")
    else:
        run_hyprctl_batch(f"{focus}; dispatch moveoutofgroup; {merge}")


def retry_ungrouped_windows(addresses: list[str]) -> None:
    expected_count = len(addresses)
    first_window_grouped_count = get_window_grouped_count(addresses[0])
    if first_window_grouped_count >= expected_count:
        return

    time.sleep(RETRY_DELAY_SECONDS)
    for address in addresses:
        grouped_count = get_window_grouped_count(address)
        if grouped_count < expected_count and grouped_count <= 1:
            dissolve_and_move_into_target_group(address)
            time.sleep(GROUP_MERGE_DELAY_SECONDS)


def group_all_tiled_windows_and_maximize(addresses: list[str]) -> None:
    if len(addresses) == 1:
        run_hyprctl_batch(
            f"dispatch focuswindow address:{addresses[0]}; dispatch fullscreen 1 set"
        )
        return

    ensure_first_window_starts_group(addresses[0])

    for address in addresses[1:]:
        dissolve_and_move_into_target_group(address)
        time.sleep(GROUP_MERGE_DELAY_SECONDS)

    retry_ungrouped_windows(addresses)
    run_hyprctl("dispatch", "fullscreen 1 set")
