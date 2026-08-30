from hyprland_ipc import run_hyprctl


NO_ADJACENT_COLUMN_RESPONSE = "no adjacent column"


def toggle_vertical_tiling() -> str:
    result = run_hyprctl("dispatch", "layoutmsg", "consume_or_expel prev").strip()
    if result == NO_ADJACENT_COLUMN_RESPONSE:
        result = run_hyprctl("dispatch", "layoutmsg", "consume_or_expel next").strip()
    return result


def main() -> None:
    toggle_vertical_tiling()


if __name__ == "__main__":
    main()
