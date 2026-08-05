import json
import urllib.error

from http_client import http_request


def arr_service_reachable(base_url):
    try:
        status_code, _ = http_request("GET", f"{base_url}/ping", {}, timeout_seconds=8)
        return status_code == 200
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


def arr_download_queue_active(arr_endpoints):
    any_endpoint_reachable = False
    for base_url, api_key in arr_endpoints:
        try:
            status_code, body = http_request(
                "GET",
                f"{base_url}/api/v3/queue?pageSize=1",
                {"X-Api-Key": api_key},
                timeout_seconds=10,
            )
        except (urllib.error.URLError, OSError, TimeoutError):
            continue
        if status_code != 200:
            continue
        any_endpoint_reachable = True
        if json.loads(body).get("totalRecords", 0) > 0:
            return True
    if not any_endpoint_reachable:
        return True
    return False
