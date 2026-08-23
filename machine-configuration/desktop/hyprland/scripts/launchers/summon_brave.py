import os
import subprocess

from hyprland_ipc import (
    get_active_workspace_id_via_activeworkspace,
    get_all_clients,
    run_hyprctl,
)

BRAVE_WINDOW_CLASS = "brave-browser"


def find_first_client_by_class(window_class: str) -> dict | None:
    for client in get_all_clients():
        if client.get("class") == window_class:
            return client
    return None


def summon_or_launch_brave() -> None:
    current_workspace_id = get_active_workspace_id_via_activeworkspace()
    client = find_first_client_by_class(BRAVE_WINDOW_CLASS)

    if client is None:
        os.execvp("brave", ["brave"])
        return

    window_address = client["address"]
    window_workspace_id = client["workspace"]["id"]

    if window_workspace_id == current_workspace_id:
        run_hyprctl("dispatch", "focuswindow", f"address:{window_address}")
        return

    subprocess.run(
        [
            "hypr-move-window-to-workspace",
            "follow",
            str(current_workspace_id),
            window_address,
        ]
    )


def main() -> None:
    summon_or_launch_brave()


if __name__ == "__main__":
    main()
