import json
import subprocess
import sys
import time

WINDOW_CLASS = "avatar-browser"
CONTROLS_TITLE = "localhost_/controls.html"
HIDDEN_WORKSPACE = "special:avatar"
WINDOW_WAIT_SECONDS = 15
FIRST_HYPRLAND_INSTANCE = "0"


def hyprctl_json(*arguments):
    return json.loads(
        subprocess.check_output(
            ["hyprctl", "--instance", FIRST_HYPRLAND_INSTANCE, "-j", *arguments],
            text=True,
        )
    )


def dispatch(*arguments):
    subprocess.run(
        ["hyprctl", "--instance", FIRST_HYPRLAND_INSTANCE, "dispatch", *arguments],
        check=True,
        capture_output=True,
    )


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


def show():
    window = wait_for_avatar_window()
    target = f"address:{window['address']}"
    monitor = next(item for item in hyprctl_json("monitors") if item["focused"])
    dispatch("movetoworkspacesilent", f"{monitor['activeWorkspace']['id']},{target}")
    if window["floating"]:
        dispatch("togglefloating", target)


def hide():
    window = avatar_window()
    if window is None:
        return
    dispatch("movetoworkspacesilent", f"{HIDDEN_WORKSPACE},address:{window['address']}")


if __name__ == "__main__":
    {"show": show, "hide": hide}[sys.argv[1]]()
