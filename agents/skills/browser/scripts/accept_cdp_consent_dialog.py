import json
import os
import subprocess
import sys
import time

DELAY_BEFORE_CLICK_SECONDS = 2
ALLOW_BUTTON_X_OFFSET_FROM_WINDOW_CENTER = 160
ALLOW_BUTTON_Y_OFFSET_FROM_WINDOW_TOP = 315
YDOTOOL_SCREEN_COORDINATE_FACTOR = 0.65


def get_chrome_window_geometry():
    result = subprocess.run(
        ["hyprctl", "clients", "-j"], capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    for client in json.loads(result.stdout):
        if client.get("class") == "google-chrome":
            client_x_position, client_y_position = client["at"]
            client_width, client_height = client["size"]
            return {
                "x": client_x_position,
                "y": client_y_position,
                "width": client_width,
                "height": client_height,
            }
    return None


def calculate_allow_button_screen_position(window_geometry):
    window_center_x = window_geometry["x"] + window_geometry["width"] // 2
    allow_x = window_center_x + ALLOW_BUTTON_X_OFFSET_FROM_WINDOW_CENTER
    allow_y = window_geometry["y"] + ALLOW_BUTTON_Y_OFFSET_FROM_WINDOW_TOP
    return allow_x, allow_y


def screen_to_ydotool_coordinates(screen_x, screen_y):
    ydotool_x = int(screen_x / YDOTOOL_SCREEN_COORDINATE_FACTOR)
    ydotool_y = int(screen_y / YDOTOOL_SCREEN_COORDINATE_FACTOR)
    return ydotool_x, ydotool_y


def ensure_ydotoold_is_running():
    result = subprocess.run(["pgrep", "ydotoold"], capture_output=True)
    if result.returncode != 0:
        subprocess.Popen(
            ["ydotoold"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        time.sleep(0.3)


def focus_chrome_window():
    subprocess.run(
        ["hyprctl", "dispatch", "focuswindow", "class:google-chrome"],
        capture_output=True,
    )
    time.sleep(0.3)


def click_at_screen_position(screen_x, screen_y):
    focus_chrome_window()
    ydotool_x, ydotool_y = screen_to_ydotool_coordinates(screen_x, screen_y)
    subprocess.run(
        [
            "ydotool",
            "mousemove",
            "--absolute",
            "-x",
            str(ydotool_x),
            "-y",
            str(ydotool_y),
        ],
        capture_output=True,
    )
    time.sleep(0.3)
    subprocess.run(["ydotool", "click", "0x40"], capture_output=True)
    time.sleep(0.05)
    subprocess.run(["ydotool", "click", "0x80"], capture_output=True)


def main():
    if not os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        print("No Hyprland session, skipping consent acceptor", file=sys.stderr)
        return

    time.sleep(DELAY_BEFORE_CLICK_SECONDS)

    window_geometry = get_chrome_window_geometry()
    if not window_geometry:
        print("No Chrome window found", file=sys.stderr)
        return

    ensure_ydotoold_is_running()

    allow_x, allow_y = calculate_allow_button_screen_position(window_geometry)
    print(
        f"Clicking Allow button at ({allow_x}, {allow_y})",
        file=sys.stderr,
    )
    click_at_screen_position(allow_x, allow_y)


if __name__ == "__main__":
    main()
