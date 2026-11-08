import time
from collections.abc import Callable

from hyprland_ipc import get_all_monitors, run_hyprctl

MODESET_SETTLE_SECONDS = 3
RELOAD_ATTEMPTS = 3


def parse_mode_resolution(mode: str) -> tuple[int, int]:
    width, height = mode.partition("@")[0].split("x")
    return int(width), int(height)


def monitor_runs_below_preferred_resolution(monitor: dict) -> bool:
    if monitor.get("disabled", False):
        return False
    available_modes = monitor.get("availableModes") or []
    if not available_modes:
        return False
    preferred_width, preferred_height = parse_mode_resolution(available_modes[0])
    return monitor["width"] * monitor["height"] < preferred_width * preferred_height


def any_monitor_runs_below_preferred_resolution(monitors: list[dict]) -> bool:
    return any(monitor_runs_below_preferred_resolution(monitor) for monitor in monitors)


def reload_hyprland_monitors() -> None:
    run_hyprctl("reload")


def restore_monitors_running_below_preferred_resolution(
    read_monitors: Callable[[], list[dict]] = get_all_monitors,
    reload_monitors: Callable[[], None] = reload_hyprland_monitors,
    wait_seconds: Callable[[float], None] = time.sleep,
) -> bool:
    for _ in range(RELOAD_ATTEMPTS):
        wait_seconds(MODESET_SETTLE_SECONDS)
        if not any_monitor_runs_below_preferred_resolution(read_monitors()):
            return True
        reload_monitors()
    wait_seconds(MODESET_SETTLE_SECONDS)
    return not any_monitor_runs_below_preferred_resolution(read_monitors())
