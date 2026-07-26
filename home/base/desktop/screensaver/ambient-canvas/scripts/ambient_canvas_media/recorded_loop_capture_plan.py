import urllib.parse

DEFAULT_CAPTURE_DURATION_SECONDS = None
DEFAULT_CAPTURE_FRAMES_PER_SECOND = 30
MINIMUM_RECORDED_BYTES_PER_SECOND = 20000
RECORD_PASS_WALL_CLOCK_CEILING_SECONDS = 900


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


def resolve_upload_wait_budget_seconds():
    return RECORD_PASS_WALL_CLOCK_CEILING_SECONDS


def resolve_minimum_recorded_bytes(duration_seconds):
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
