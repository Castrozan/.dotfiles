import json
import os
import re
import subprocess

CHROMIUM_BROWSER_CANDIDATES = ["Google Chrome", "Brave Browser"]
FALLBACK_SCREEN_WIDTH = 1440
FALLBACK_SCREEN_HEIGHT = 900
CENTERED_WINDOW_SCREEN_FRACTION = 0.72
DISPLAY_REPORT_COMMAND = ["/usr/sbin/system_profiler", "SPDisplaysDataType", "-json"]
DISPLAY_REPORT_TIMEOUT_SECONDS = 30
DISPLAY_POINT_RESOLUTION_KEY = "_spdisplays_resolution"
MAIN_DISPLAY_FLAG_VALUE = "spdisplays_yes"
DISPLAY_RESOLUTION_PATTERN = re.compile(r"(\d+)\s*x\s*(\d+)")


def resolve_chromium_browser_application():
    for application_name in CHROMIUM_BROWSER_CANDIDATES:
        if os.path.isdir(f"/Applications/{application_name}.app"):
            return application_name
    return None


def resolve_browser_executable_path(application_name):
    return f"/Applications/{application_name}.app/Contents/MacOS/{application_name}"


def parse_display_point_resolution(resolution_text):
    resolution_match = DISPLAY_RESOLUTION_PATTERN.search(resolution_text)
    if resolution_match is None:
        return None
    return int(resolution_match.group(1)), int(resolution_match.group(2))


def select_main_display_entry(display_report):
    attached_displays = [
        screen
        for graphics_device in display_report.get("SPDisplaysDataType", [])
        for screen in graphics_device.get("spdisplays_ndrvs", [])
        if DISPLAY_POINT_RESOLUTION_KEY in screen
    ]
    for screen in attached_displays:
        if screen.get("spdisplays_main") == MAIN_DISPLAY_FLAG_VALUE:
            return screen
    return attached_displays[0] if attached_displays else None


def parse_screen_dimensions(display_report_json):
    try:
        main_display = select_main_display_entry(json.loads(display_report_json))
    except (TypeError, ValueError, AttributeError):
        return FALLBACK_SCREEN_WIDTH, FALLBACK_SCREEN_HEIGHT
    if main_display is None:
        return FALLBACK_SCREEN_WIDTH, FALLBACK_SCREEN_HEIGHT
    point_resolution = parse_display_point_resolution(
        main_display[DISPLAY_POINT_RESOLUTION_KEY]
    )
    if point_resolution is None:
        return FALLBACK_SCREEN_WIDTH, FALLBACK_SCREEN_HEIGHT
    return point_resolution


def read_screen_dimensions():
    try:
        completed = subprocess.run(
            DISPLAY_REPORT_COMMAND,
            capture_output=True,
            text=True,
            check=True,
            timeout=DISPLAY_REPORT_TIMEOUT_SECONDS,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return FALLBACK_SCREEN_WIDTH, FALLBACK_SCREEN_HEIGHT
    return parse_screen_dimensions(completed.stdout)


def resolve_centered_window_geometry(screen_width, screen_height):
    window_width = int(screen_width * CENTERED_WINDOW_SCREEN_FRACTION)
    window_height = int(screen_height * CENTERED_WINDOW_SCREEN_FRACTION)
    window_left = (screen_width - window_width) // 2
    window_top = (screen_height - window_height) // 2
    return window_width, window_height, window_left, window_top
