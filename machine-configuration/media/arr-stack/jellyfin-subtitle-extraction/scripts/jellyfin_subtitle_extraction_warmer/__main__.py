import os
import time
import urllib.error

from jellyfin_http_client import (
    jellyfin_is_reachable,
    list_active_sessions,
    list_video_items,
    read_api_key,
    request_body,
)
from subtitle_extraction_cache import (
    someone_is_watching,
    subtitle_stream_request_path,
    unextracted_subtitle_streams_of_item,
)

LOG_PREFIX = "jellyfin-subtitle-extraction-warmer"
QUIET_POLLS_BEFORE_SWEEPING = 2


def extract_streams_of_item(base_url, api_key, item, unextracted_streams):
    extracted_count = 0
    for unextracted_stream in unextracted_streams:
        try:
            request_body(
                base_url, api_key, subtitle_stream_request_path(unextracted_stream)
            )
            extracted_count += 1
        except (urllib.error.URLError, OSError) as extraction_failure:
            print(
                f"{LOG_PREFIX}: stream {unextracted_stream['streamIndex']} of "
                f"'{item.get('Name')}' failed: {extraction_failure}"
            )
    return extracted_count


def sweep(
    base_url,
    api_key,
    jellyfin_data_directory,
    item_budget,
    pause_seconds,
    yield_to_playback=True,
):
    extracted_streams = 0
    extracted_items = 0
    for item in list_video_items(base_url, api_key):
        unextracted_streams = unextracted_subtitle_streams_of_item(
            item, jellyfin_data_directory
        )
        if not unextracted_streams:
            continue
        if extracted_items >= item_budget:
            print(f"{LOG_PREFIX}: sweep budget of {item_budget} items reached")
            break
        if yield_to_playback and someone_is_watching(
            list_active_sessions(base_url, api_key)
        ):
            print(f"{LOG_PREFIX}: sweep stopped, playback started")
            break
        extracted_streams += extract_streams_of_item(
            base_url, api_key, item, unextracted_streams
        )
        extracted_items += 1
        print(
            f"{LOG_PREFIX}: extracted {len(unextracted_streams)} subtitle streams "
            f"for '{item.get('Name')}'"
        )
        time.sleep(pause_seconds)
    return extracted_items, extracted_streams


def wait_for_a_quiet_server(base_url, api_key, poll_seconds, deadline_seconds):
    consecutive_quiet_polls = 0
    waited_seconds = 0
    while True:
        if someone_is_watching(list_active_sessions(base_url, api_key)):
            consecutive_quiet_polls = 0
        else:
            consecutive_quiet_polls += 1
            if consecutive_quiet_polls >= QUIET_POLLS_BEFORE_SWEEPING:
                return True
        if waited_seconds >= deadline_seconds:
            return False
        time.sleep(poll_seconds)
        waited_seconds += poll_seconds


def main():
    base_url = os.environ["JELLYFIN_SUBTITLE_EXTRACTION_WARMER_BASE_URL"]
    api_key = read_api_key(
        os.environ["JELLYFIN_SUBTITLE_EXTRACTION_WARMER_API_KEY_FILE"]
    )
    jellyfin_data_directory = os.environ[
        "JELLYFIN_SUBTITLE_EXTRACTION_WARMER_DATA_DIRECTORY"
    ]
    item_budget = int(os.environ["JELLYFIN_SUBTITLE_EXTRACTION_WARMER_ITEM_BUDGET"])
    busy_item_budget = int(
        os.environ["JELLYFIN_SUBTITLE_EXTRACTION_WARMER_BUSY_ITEM_BUDGET"]
    )
    pause_seconds = float(
        os.environ["JELLYFIN_SUBTITLE_EXTRACTION_WARMER_PAUSE_SECONDS"]
    )
    quiet_poll_seconds = float(
        os.environ["JELLYFIN_SUBTITLE_EXTRACTION_WARMER_QUIET_POLL_SECONDS"]
    )
    quiet_wait_seconds = float(
        os.environ["JELLYFIN_SUBTITLE_EXTRACTION_WARMER_QUIET_WAIT_SECONDS"]
    )
    if not jellyfin_is_reachable(base_url, api_key):
        print(f"{LOG_PREFIX}: skipped, jellyfin is not reachable")
        return
    try:
        server_went_quiet = wait_for_a_quiet_server(
            base_url, api_key, quiet_poll_seconds, quiet_wait_seconds
        )
        if not server_went_quiet:
            print(
                f"{LOG_PREFIX}: no gap between playbacks, extracting "
                f"{busy_item_budget} items alongside the stream"
            )
        extracted_items, extracted_streams = sweep(
            base_url,
            api_key,
            jellyfin_data_directory,
            item_budget if server_went_quiet else busy_item_budget,
            pause_seconds,
            yield_to_playback=server_went_quiet,
        )
    except (urllib.error.URLError, OSError) as jellyfin_failure:
        print(f"{LOG_PREFIX}: stopped, jellyfin stopped answering: {jellyfin_failure}")
        return
    print(
        f"{LOG_PREFIX}: sweep finished, {extracted_streams} subtitle streams "
        f"extracted across {extracted_items} items"
    )


if __name__ == "__main__":
    main()
