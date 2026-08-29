from typing import Any

from hyprland_ipc import run_hyprctl, run_hyprctl_json

VALID_DIRECTIONS = frozenset({"left", "right", "down", "up"})
HORIZONTAL_DIRECTIONS = frozenset({"left", "right"})
DEFAULT_DIRECTION = "right"
VERTICAL_DIRECTION = "down"


def get_current_scrolling_direction() -> str:
    option: dict[str, Any] = run_hyprctl_json("getoption", "scrolling:direction") or {}
    direction = option.get("str")
    return direction if direction in VALID_DIRECTIONS else DEFAULT_DIRECTION


def apply_scrolling_direction(direction: str) -> None:
    run_hyprctl("keyword", "scrolling:direction", direction)
    run_hyprctl("dispatch", "layoutmsg", "fit active")


def toggle_scrolling_direction() -> str:
    current = get_current_scrolling_direction()
    target = (
        VERTICAL_DIRECTION if current in HORIZONTAL_DIRECTIONS else DEFAULT_DIRECTION
    )
    apply_scrolling_direction(target)
    return target


def main() -> None:
    toggle_scrolling_direction()


if __name__ == "__main__":
    main()
