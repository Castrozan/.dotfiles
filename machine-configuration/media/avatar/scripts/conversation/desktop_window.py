import json
import subprocess
import sys
import time

WINDOW_CLASS = "avatar-browser"
CONTROLS_TITLE = "localhost_/controls.html"
HIDDEN_WORKSPACE = "special:avatar"
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 360
SCREEN_MARGIN = 24
WINDOW_WAIT_SECONDS = 15
PLACEMENT_ATTEMPTS = 25
PLACEMENT_SETTLE_SECONDS = 0.2


def hyprctl_json(*arguments):
    return json.loads(subprocess.check_output(["hyprctl", "-j", *arguments], text=True))


def dispatch(*arguments):
    subprocess.run(["hyprctl", "dispatch", *arguments], check=True, capture_output=True)


def avatar_window():
    return next(
        (
            client
            for client in hyprctl_json("clients")
            if client["class"] == WINDOW_CLASS and client["title"] != CONTROLS_TITLE
        ),
        None,
    )


def wait_for_avatar_window():
    deadline = time.monotonic() + WINDOW_WAIT_SECONDS
    while time.monotonic() < deadline:
        if window := avatar_window():
            return window
        time.sleep(0.2)
    raise TimeoutError("The avatar window did not appear")


def corner_of(monitor):
    return (
        monitor["x"]
        + int(monitor["width"] / monitor["scale"])
        - WINDOW_WIDTH
        - SCREEN_MARGIN,
        monitor["y"]
        + int(monitor["height"] / monitor["scale"])
        - WINDOW_HEIGHT
        - SCREEN_MARGIN,
    )


def place(target, x, y):
    for _ in range(PLACEMENT_ATTEMPTS):
        dispatch("movewindowpixel", f"exact {x} {y},{target}")
        time.sleep(PLACEMENT_SETTLE_SECONDS)
        if avatar_window()["at"] == [x, y]:
            return
    raise TimeoutError("The avatar window did not reach its corner")


def show():
    window = wait_for_avatar_window()
    target = f"address:{window['address']}"
    monitor = next(item for item in hyprctl_json("monitors") if item["focused"])
    x, y = corner_of(monitor)
    dispatch("movetoworkspacesilent", f"{monitor['activeWorkspace']['id']},{target}")
    if not window["floating"]:
        dispatch("togglefloating", target)
    dispatch("resizewindowpixel", f"exact {WINDOW_WIDTH} {WINDOW_HEIGHT},{target}")
    place(target, x, y)
    if not window["pinned"]:
        dispatch("pin", target)


def hide():
    window = avatar_window()
    if window is None:
        return
    target = f"address:{window['address']}"
    if window["pinned"]:
        dispatch("pin", target)
    dispatch("movetoworkspacesilent", f"{HIDDEN_WORKSPACE},{target}")


if __name__ == "__main__":
    {"show": show, "hide": hide}[sys.argv[1]]()
