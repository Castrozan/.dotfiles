import os
import subprocess
import time
from pathlib import Path

from hyprland_ipc import (
    get_active_window,
    get_all_clients,
    get_focused_monitor,
    run_hyprctl,
    run_hyprctl_batch,
)

STATE_DIR = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "hyprland-show-desktop"


def find_grouped_window_on_workspace(workspace_id: int) -> str | None:
    for client in get_all_clients():
        if (
            client.get("workspace", {}).get("id") == workspace_id
            and not client.get("floating", False)
            and len(client.get("grouped", [])) > 1
        ):
            return client.get("address")
    return None


def dissolve_groups_on_workspace(workspace_id: int) -> None:
    grouped_window_address = find_grouped_window_on_workspace(workspace_id)
    if grouped_window_address:
        run_hyprctl_batch(
            f"dispatch focuswindow address:{grouped_window_address};"
            " dispatch togglegroup"
        )


def hide_all_workspace_windows_to_special_desktop(workspace_id: int) -> None:
    state_file = STATE_DIR / f"ws-{workspace_id}"
    focus_file = STATE_DIR / f"focus-{workspace_id}"

    active_window = get_active_window()
    active_address = active_window.get("address") if active_window else None

    window_addresses = [
        client.get("address")
        for client in get_all_clients()
        if client.get("workspace", {}).get("id") == workspace_id
    ]

    if not window_addresses:
        return

    if active_address and active_address != "null":
        focus_file.write_text(active_address)
    state_file.write_text("\n".join(window_addresses))

    dissolve_groups_on_workspace(workspace_id)

    hide_batch = "; ".join(
        f"dispatch movetoworkspacesilent special:desktop,address:{addr}"
        for addr in window_addresses
    )
    run_hyprctl_batch(hide_batch)


def restore_hidden_windows_and_maximize(workspace_id: int) -> None:
    state_file = STATE_DIR / f"ws-{workspace_id}"
    focus_file = STATE_DIR / f"focus-{workspace_id}"

    window_addresses = state_file.read_text().splitlines()

    move_batch = "; ".join(
        f"dispatch movetoworkspacesilent {workspace_id},address:{addr}"
        for addr in window_addresses
        if addr.strip()
    )
    run_hyprctl_batch(move_batch)

    time.sleep(0.5)

    if focus_file.exists():
        saved_focus_address = focus_file.read_text().strip()
        run_hyprctl("dispatch", f"focuswindow address:{saved_focus_address}")
        focus_file.unlink()

    state_file.unlink()

    subprocess.run(["hypr-ensure-workspace-grouped"])


def main() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    monitor = get_focused_monitor()
    if not monitor:
        return
    current_workspace_id = monitor.get("activeWorkspace", {}).get("id")
    if current_workspace_id is None:
        return

    state_file = STATE_DIR / f"ws-{current_workspace_id}"

    if state_file.exists():
        restore_hidden_windows_and_maximize(current_workspace_id)
    else:
        hide_all_workspace_windows_to_special_desktop(current_workspace_id)


if __name__ == "__main__":
    main()
