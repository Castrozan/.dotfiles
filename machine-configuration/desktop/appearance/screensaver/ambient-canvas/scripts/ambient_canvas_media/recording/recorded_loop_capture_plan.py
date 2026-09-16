import urllib.parse

import ambient_canvas_browser

DEFAULT_CAPTURE_DURATION_SECONDS = None
DEFAULT_CAPTURE_FRAMES_PER_SECOND = 30
CAPTURE_PIXEL_HEIGHT = 1080
FALLBACK_CAPTURE_PIXEL_WIDTH = 1920
MINIMUM_RECORDED_BYTES_PER_SECOND = 2000
RECORD_PASS_WALL_CLOCK_CEILING_SECONDS = 1800


def resolve_capture_pixel_dimensions(screen_width, screen_height):
    if screen_width <= 0 or screen_height <= 0:
        return FALLBACK_CAPTURE_PIXEL_WIDTH, CAPTURE_PIXEL_HEIGHT
    fitted_width = CAPTURE_PIXEL_HEIGHT * screen_width / screen_height
    return max(2, round(fitted_width / 2) * 2), CAPTURE_PIXEL_HEIGHT


def format_capture_signature(capture_pixel_dimensions):
    capture_pixel_width, capture_pixel_height = capture_pixel_dimensions
    return f"{capture_pixel_width}x{capture_pixel_height}"


def build_record_index_url(
    index_file_url,
    upload_url,
    duration_seconds,
    frames_per_second,
    capture_pixel_dimensions,
    theme_background_hex,
):
    capture_pixel_width, capture_pixel_height = capture_pixel_dimensions
    record_query_parameters = {
        "record": "1",
        "fps": str(frames_per_second),
        "width": str(capture_pixel_width),
        "height": str(capture_pixel_height),
        "uploadUrl": upload_url,
        "themeBackground": theme_background_hex,
    }
    if duration_seconds is not None:
        record_query_parameters["seconds"] = str(duration_seconds)
    record_query = urllib.parse.urlencode(record_query_parameters)
    return f"{index_file_url}?{record_query}"


def resolve_upload_wait_budget_seconds():
    return RECORD_PASS_WALL_CLOCK_CEILING_SECONDS


def resolve_minimum_recorded_bytes(duration_seconds):
    return duration_seconds * MINIMUM_RECORDED_BYTES_PER_SECOND


def build_record_browser_arguments(
    browser_executable_path, record_index_url, throwaway_profile_directory, geometry
):
    window_width, window_height, window_left, window_top = geometry
    platform_arguments = (
        ["--disable-accelerated-video-decode"]
        if not ambient_canvas_browser.resolve_platform().startswith("darwin")
        else []
    )
    return [
        browser_executable_path,
        f"--app={record_index_url}",
        f"--user-data-dir={throwaway_profile_directory}",
        f"--window-size={window_width},{window_height}",
        f"--window-position={window_left},{window_top}",
        "--no-first-run",
        "--no-default-browser-check",
        "--autoplay-policy=no-user-gesture-required",
        "--disable-translate",
        "--use-gl=angle",
        *platform_arguments,
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-features=CalculateNativeWinOcclusion",
    ]
