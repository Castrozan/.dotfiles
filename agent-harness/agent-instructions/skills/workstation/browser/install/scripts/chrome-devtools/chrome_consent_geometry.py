import json
import time

from chrome_consent_target import (
    current_target,
    cursor_position,
    focused_window,
    run_tool,
    target_signature,
)


def monitor_rectangles(configuration):
    monitors = json.loads(run_tool(configuration, "hyprctl", "-j", "monitors"))
    return [
        (monitor["x"], monitor["y"], monitor["width"], monitor["height"])
        for monitor in monitors
        if not monitor.get("disabled")
        and monitor["scale"] == 1
        and monitor.get("transform", 0) == 0
    ]


def containing_monitor(target, rectangles):
    left, top = target["at"]
    width, height = target["size"]
    matches = [
        rectangle
        for rectangle in rectangles
        if rectangle[0] <= left
        and rectangle[1] <= top
        and left + width <= rectangle[0] + rectangle[2]
        and top + height <= rectangle[1] + rectangle[3]
    ]
    return matches[0] if len(matches) == 1 else None


def clamp_cursor(position, rectangle):
    left, top, width, height = rectangle
    return (
        min(max(position[0], left), left + width - 1),
        min(max(position[1], top), top + height - 1),
    )


def require_settling_target(configuration, target, original_cursor):
    if (
        focused_window(configuration) != target["address"]
        or cursor_position(configuration) != original_cursor
    ):
        raise RuntimeError("User focus or cursor changed while Chrome was settling")
    observed = current_target(configuration)
    if any(observed[key] != target[key] for key in ("address", "pid", "process_start")):
        raise RuntimeError("Chrome process changed while its geometry was settling")
    return observed


def settle_focused_target(configuration, target, original_cursor, deadline):
    rectangles = monitor_rectangles(configuration)
    deadline = min(deadline, time.monotonic() + 2)
    previous = None
    stable_since = time.monotonic()
    while time.monotonic() < deadline:
        observed = require_settling_target(configuration, target, original_cursor)
        signature = target_signature(observed)
        rectangle = containing_monitor(observed, rectangles)
        if signature != previous:
            stable_since = time.monotonic()
        elif rectangle is not None and time.monotonic() - stable_since >= 0.15:
            return observed, rectangle
        previous = signature
        time.sleep(min(0.05, max(0, deadline - time.monotonic())))
    raise RuntimeError("Chrome geometry did not settle visibly before the deadline")
