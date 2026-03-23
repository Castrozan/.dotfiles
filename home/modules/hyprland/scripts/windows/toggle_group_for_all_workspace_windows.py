from hyprland_ipc import get_active_workspace_id, run_hyprctl
from workspace_grouping import (
    all_tiled_windows_are_in_single_group_on_workspace,
    get_tiled_window_addresses_on_workspace,
    group_all_tiled_windows_and_maximize,
)


def main() -> None:
    workspace_id = get_active_workspace_id()
    if workspace_id is None:
        return

    if all_tiled_windows_are_in_single_group_on_workspace(workspace_id):
        run_hyprctl("dispatch", "togglegroup")
        return

    addresses = get_tiled_window_addresses_on_workspace(workspace_id)
    if not addresses:
        return

    group_all_tiled_windows_and_maximize(addresses)


if __name__ == "__main__":
    main()
