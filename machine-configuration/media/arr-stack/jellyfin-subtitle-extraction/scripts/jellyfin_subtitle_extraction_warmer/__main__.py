import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from subtitle_extraction_cache import (
    someone_is_watching,
    subtitle_stream_request_path,
    unextracted_subtitle_streams_of_item,
)

LOG_PREFIX = "jellyfin-subtitle-extraction-warmer"
EXTRACTION_REQUEST_TIMEOUT_SECONDS = 600
ITEM_PAGE_SIZE = 200
QUIET_POLLS_BEFORE_SWEEPING = 2


def read_api_key(api_key_file_path):
    with open(api_key_file_path, encoding="utf-8") as handle:
        return handle.read().strip()


def request_body(base_url, api_key, path):
    request = urllib.request.Request(
        f"{base_url}{path}", headers={"X-Emby-Token": api_key}
    )
    with urllib.request.urlopen(
        request, timeout=EXTRACTION_REQUEST_TIMEOUT_SECONDS
    ) as response:
        return response.read()


def request_json(base_url, api_key, path):
    body = request_body(base_url, api_key, path)
    return json.loads(body) if body else None


def jellyfin_is_reachable(base_url, api_key):
    try:
        request_json(base_url, api_key, "/System/Info")
        return True
    except (urllib.error.URLError, OSError):
        return False


def list_active_sessions(base_url, api_key):
    return request_json(base_url, api_key, "/Sessions") or []


def list_video_items(base_url, api_key):
    video_items = []
    start_index = 0
    while True:
        query_string = urllib.parse.urlencode(
            {
                "recursive": "true",
                "includeItemTypes": "Movie,Episode",
                "fields": "MediaSources",
                "enableTotalRecordCount": "false",
                "startIndex": start_index,
                "limit": ITEM_PAGE_SIZE,
            }
        )
        page_items = (
            request_json(base_url, api_key, f"/Items?{query_string}") or {}
        ).get("Items") or []
        video_items.extend(page_items)
        if len(page_items) < ITEM_PAGE_SIZE:
            return video_items
        start_index += ITEM_PAGE_SIZE


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


def sweep(base_url, api_key, jellyfin_data_directory, item_budget, pause_seconds):
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
        if someone_is_watching(list_active_sessions(base_url, api_key)):
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
    if not wait_for_a_quiet_server(
        base_url, api_key, quiet_poll_seconds, quiet_wait_seconds
    ):
        print(f"{LOG_PREFIX}: gave up waiting for a gap between playbacks")
        return
    extracted_items, extracted_streams = sweep(
        base_url, api_key, jellyfin_data_directory, item_budget, pause_seconds
    )
    print(
        f"{LOG_PREFIX}: sweep finished, {extracted_streams} subtitle streams "
        f"extracted across {extracted_items} items"
    )


if __name__ == "__main__":
    main()
