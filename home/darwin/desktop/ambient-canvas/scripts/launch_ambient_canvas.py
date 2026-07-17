import os
import subprocess
import sys

CHROMIUM_BROWSER_CANDIDATES = ["Google Chrome", "Brave Browser"]
AMBIENT_CANVAS_PROFILE_DIRECTORY = os.path.expanduser(
    "~/.local/state/ambient-canvas/profile"
)
CENTERED_WINDOW_SCREEN_FRACTION = 0.72
FALLBACK_SCREEN_WIDTH = 1440
FALLBACK_SCREEN_HEIGHT = 900


def resolve_chromium_browser_application():
    for application_name in CHROMIUM_BROWSER_CANDIDATES:
        if os.path.isdir(f"/Applications/{application_name}.app"):
            return application_name
    return None


def resolve_index_file_url():
    index_path = os.environ.get("AMBIENT_CANVAS_INDEX")
    if not index_path or not os.path.isfile(index_path):
        return None
    return "file://" + index_path


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


def build_browser_arguments(browser_application, index_url, geometry):
    window_width, window_height, window_left, window_top = geometry
    return [
        "open",
        "-na",
        browser_application,
        "--args",
        f"--app={index_url}",
        f"--user-data-dir={AMBIENT_CANVAS_PROFILE_DIRECTORY}",
        f"--window-size={window_width},{window_height}",
        f"--window-position={window_left},{window_top}",
        "--no-first-run",
        "--no-default-browser-check",
        "--autoplay-policy=no-user-gesture-required",
        "--disable-translate",
    ]


def main():
    browser_application = resolve_chromium_browser_application()
    if browser_application is None:
        print("ambient-canvas: no Chromium browser installed", file=sys.stderr)
        return 1
    index_url = resolve_index_file_url()
    if index_url is None:
        print("ambient-canvas: web assets not found", file=sys.stderr)
        return 1
    os.makedirs(AMBIENT_CANVAS_PROFILE_DIRECTORY, exist_ok=True)
    geometry = resolve_centered_window_geometry(*read_screen_dimensions())
    subprocess.run(
        build_browser_arguments(browser_application, index_url, geometry),
        check=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
