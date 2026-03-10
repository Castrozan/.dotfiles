import sys

from hyprland_ipc import get_active_workspace_id, get_all_clients


def all_tiled_windows_on_active_workspace_are_in_single_group() -> bool:
    workspace_id = get_active_workspace_id()
    if workspace_id is None:
        return False

    tiled_windows = [
        client
        for client in get_all_clients()
        if client.get("workspace", {}).get("id") == workspace_id
        and not client.get("floating", False)
    ]

    if not tiled_windows:
        return False

    total = len(tiled_windows)
    max_group_size = max(len(c.get("grouped", [])) for c in tiled_windows)
    return max_group_size == total


def main() -> None:
    sys.exit(0 if all_tiled_windows_on_active_workspace_are_in_single_group() else 1)


if __name__ == "__main__":
    main()
