import json
import urllib.error

from http_client import http_request
from runtime_environment import log, parse_iso8601_to_epoch

UNREACHABLE_ERRORS = (urllib.error.URLError, OSError, TimeoutError)


def get_json(base_url, api_key, path):
    try:
        status_code, body = http_request(
            "GET", f"{base_url}{path}", {"X-Api-Key": api_key}
        )
    except UNREACHABLE_ERRORS:
        return None
    if status_code != 200:
        return None
    return json.loads(body)


def active_indexer_count(base_url, api_key, now_epoch):
    indexers = get_json(base_url, api_key, "/api/v3/indexer")
    if indexers is None:
        return None
    searchable_indexer_ids = {
        indexer.get("id")
        for indexer in indexers
        if indexer.get("enableAutomaticSearch")
    }
    if not searchable_indexer_ids:
        return 0
    indexer_statuses = get_json(base_url, api_key, "/api/v3/indexerstatus") or []
    disabled_indexer_ids = {
        status.get("indexerId")
        for status in indexer_statuses
        if status.get("disabledTill")
        and parse_iso8601_to_epoch(status["disabledTill"]) > now_epoch
    }
    return len(searchable_indexer_ids - disabled_indexer_ids)


def monitored_missing_records(base_url, api_key):
    response = get_json(
        base_url,
        api_key,
        "/api/v3/wanted/missing?pageSize=1000&monitored=true",
    )
    if response is None:
        return None
    return response.get("records", [])


def queued_records(base_url, api_key):
    response = get_json(base_url, api_key, "/api/v3/queue?pageSize=1000")
    if response is None:
        return None
    return response.get("records", [])


def series_records(base_url, api_key):
    return get_json(base_url, api_key, "/api/v3/series")


def trigger_search(base_url, api_key, payload, item_count, dry_run):
    command_name = payload["name"]
    if dry_run:
        log(f"[dry-run] would send {command_name} for {item_count} items to {base_url}")
        return True
    try:
        status_code, _ = http_request(
            "POST",
            f"{base_url}/api/v3/command",
            {"X-Api-Key": api_key, "Content-Type": "application/json"},
            body=json.dumps(payload),
        )
    except UNREACHABLE_ERRORS:
        log(
            f"missing-search sweep: {base_url} unreachable while sending "
            f"{command_name}; deferring"
        )
        return False
    if not 200 <= status_code < 300:
        log(
            f"missing-search sweep: {base_url} rejected {command_name} with "
            f"HTTP {status_code}; deferring"
        )
        return False
    return True
