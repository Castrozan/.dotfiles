import json
from datetime import datetime

from http_client import http_request


def parse_iso8601_to_epoch(value):
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized).timestamp()


def actionable_requests(base_url, api_key, now_epoch, recent_pending_window_seconds):
    status_code, body = http_request(
        "GET",
        f"{base_url}/api/v1/request?take=100&filter=all&sort=added",
        {"X-Api-Key": api_key},
    )
    if status_code != 200:
        raise SystemExit(f"jellyseerr request listing returned {status_code}")
    results = json.loads(body).get("results", [])
    request_status_pending = 1
    request_status_failed = 4
    recent_pending_request_ids = []
    failed_request_ids = []
    for entry in results:
        entry_status = entry.get("status")
        entry_id = entry.get("id")
        if entry_status == request_status_failed:
            failed_request_ids.append(entry_id)
        elif entry_status == request_status_pending:
            created_at = entry.get("createdAt")
            age_seconds = None
            if created_at:
                age_seconds = now_epoch - parse_iso8601_to_epoch(created_at)
            if age_seconds is None or age_seconds <= recent_pending_window_seconds:
                recent_pending_request_ids.append(entry_id)
    return recent_pending_request_ids, failed_request_ids


def retry_request(base_url, api_key, request_id):
    status_code, _ = http_request(
        "POST",
        f"{base_url}/api/v1/request/{request_id}/retry",
        {"X-Api-Key": api_key},
    )
    return status_code
