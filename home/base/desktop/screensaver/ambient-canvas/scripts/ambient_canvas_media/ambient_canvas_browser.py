import os
import subprocess

CHROMIUM_BROWSER_CANDIDATES = ["Google Chrome", "Brave Browser"]
FALLBACK_SCREEN_WIDTH = 1440
FALLBACK_SCREEN_HEIGHT = 900
CENTERED_WINDOW_SCREEN_FRACTION = 0.72


def resolve_chromium_browser_application():
    for application_name in CHROMIUM_BROWSER_CANDIDATES:
        if os.path.isdir(f"/Applications/{application_name}.app"):
            return application_name
    return None


def resolve_browser_executable_path(application_name):
    return f"/Applications/{application_name}.app/Contents/MacOS/{application_name}"


def parse_desktop_bounds(bounds_text):
    left, top, right, bottom = (int(value.strip()) for value in bounds_text.split(","))
    return right - left, bottom - top


def read_screen_dimensions():
    try:
        completed = subprocess.run(
            [
                "osascript",
                "-e",
                'tell application "Finder" to get bounds of window of desktop',
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return parse_desktop_bounds(completed.stdout.strip())
    except (subprocess.CalledProcessError, ValueError, OSError):
        return FALLBACK_SCREEN_WIDTH, FALLBACK_SCREEN_HEIGHT


def resolve_centered_window_geometry(screen_width, screen_height):
    window_width = int(screen_width * CENTERED_WINDOW_SCREEN_FRACTION)
    window_height = int(screen_height * CENTERED_WINDOW_SCREEN_FRACTION)
    window_left = (screen_width - window_width) // 2
    window_top = (screen_height - window_height) // 2
    return window_width, window_height, window_left, window_top
