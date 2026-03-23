import sys

from hyprland_ipc import get_active_workspace_id
from workspace_grouping import all_tiled_windows_are_in_single_group_on_workspace


def main() -> None:
    workspace_id = get_active_workspace_id()
    is_grouped = (
        workspace_id is not None
        and all_tiled_windows_are_in_single_group_on_workspace(workspace_id)
    )
    sys.exit(0 if is_grouped else 1)


if __name__ == "__main__":
    main()
