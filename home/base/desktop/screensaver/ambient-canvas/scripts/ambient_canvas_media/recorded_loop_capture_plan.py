import urllib.parse

DEFAULT_CAPTURE_DURATION_SECONDS = None
DEFAULT_CAPTURE_FRAMES_PER_SECOND = 30
CHROME_STARTUP_AND_UPLOAD_GRACE_SECONDS = 45
DETERMINISTIC_RENDER_WALL_CLOCK_MULTIPLIER = 4
MINIMUM_RECORDED_BYTES_PER_SECOND = 20000
PLAYLIST_DERIVED_RENDER_WALL_CLOCK_CEILING_SECONDS = 900
PLAYLIST_DERIVED_MINIMUM_RECORDED_BYTES = 200000


def build_record_index_url(
    index_file_url, upload_url, duration_seconds, frames_per_second
):
    record_query_parameters = {
        "record": "1",
        "fps": str(frames_per_second),
        "uploadUrl": upload_url,
    }
    if duration_seconds is not None:
        record_query_parameters["seconds"] = str(duration_seconds)
    record_query = urllib.parse.urlencode(record_query_parameters)
    return f"{index_file_url}?{record_query}"


def resolve_upload_wait_budget_seconds(duration_seconds):
    if duration_seconds is None:
        return PLAYLIST_DERIVED_RENDER_WALL_CLOCK_CEILING_SECONDS
    return (
        duration_seconds * DETERMINISTIC_RENDER_WALL_CLOCK_MULTIPLIER
        + CHROME_STARTUP_AND_UPLOAD_GRACE_SECONDS
    )


def resolve_minimum_recorded_bytes(duration_seconds):
    if duration_seconds is None:
        return PLAYLIST_DERIVED_MINIMUM_RECORDED_BYTES
    return duration_seconds * MINIMUM_RECORDED_BYTES_PER_SECOND


def build_record_browser_arguments(
    browser_executable_path, record_index_url, throwaway_profile_directory, geometry
):
    window_width, window_height, window_left, window_top = geometry
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
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-features=CalculateNativeWinOcclusion",
    ]
