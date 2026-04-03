import sys

from hyprland_ipc import run_hyprctl_batch

USAGE = (
    "usage: hypr-move-window-to-workspace <silent|follow> <workspace> [window-address]"
)


def build_move_window_to_workspace_commands(
    mode: str, target_workspace: str, window_address: str | None
) -> str:
    commands = []

    if window_address:
        commands.append(f"dispatch focuswindow address:{window_address}")

    commands.append(f"dispatch movetoworkspace {target_workspace}")

    if mode == "silent":
        commands.append("dispatch workspace previous")

    return "; ".join(commands)


def main() -> None:
    if len(sys.argv) < 3:
        print(USAGE, file=sys.stderr)
        sys.exit(1)

    mode = sys.argv[1]
    target_workspace = sys.argv[2]
    window_address = sys.argv[3] if len(sys.argv) > 3 else None

    commands = build_move_window_to_workspace_commands(
        mode, target_workspace, window_address
    )
    run_hyprctl_batch(commands)


if __name__ == "__main__":
    main()
