import json
import urllib.error
import urllib.parse
import urllib.request

EXTRACTION_REQUEST_TIMEOUT_SECONDS = 600
ITEM_PAGE_SIZE = 200


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
