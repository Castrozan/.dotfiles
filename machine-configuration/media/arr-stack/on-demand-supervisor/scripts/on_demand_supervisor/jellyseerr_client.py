import json

from http_client import http_request
from runtime_environment import parse_iso8601_to_epoch


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
        _collect_actionable_request_ids(
            entry,
            now_epoch,
            recent_pending_window_seconds,
            request_status_pending,
            request_status_failed,
            recent_pending_request_ids,
            failed_request_ids,
        )
    return recent_pending_request_ids, failed_request_ids


def _collect_actionable_request_ids(
    entry,
    now_epoch,
    recent_pending_window_seconds,
    request_status_pending,
    request_status_failed,
    recent_pending_request_ids,
    failed_request_ids,
):
    entry_status = entry.get("status")
    entry_id = entry.get("id")
    if entry_status == request_status_failed:
        failed_request_ids.append(entry_id)
        return
    if entry_status != request_status_pending:
        return
    _append_recent_pending_request_id(
        entry,
        entry_id,
        now_epoch,
        recent_pending_window_seconds,
        recent_pending_request_ids,
    )


def _append_recent_pending_request_id(
    entry,
    entry_id,
    now_epoch,
    recent_pending_window_seconds,
    recent_pending_request_ids,
):
    created_at = entry.get("createdAt")
    age_seconds = None
    if created_at:
        age_seconds = now_epoch - parse_iso8601_to_epoch(created_at)
    if age_seconds is None or age_seconds <= recent_pending_window_seconds:
        recent_pending_request_ids.append(entry_id)


def retry_request(base_url, api_key, request_id):
    status_code, _ = http_request(
        "POST",
        f"{base_url}/api/v1/request/{request_id}/retry",
        {"X-Api-Key": api_key},
    )
    return status_code


def has_actionable_request_ids(recent_pending_request_ids, failed_request_ids):
    return bool(recent_pending_request_ids) or bool(failed_request_ids)


def retry_failed_request_ids(
    jellyseerr_endpoint,
    failed_request_ids,
    is_radarr_reachable,
    dry_run,
    retry_request_call,
    log_message,
):
    jellyseerr_url, jellyseerr_api_key = jellyseerr_endpoint
    if failed_request_ids and is_radarr_reachable():
        for request_id in failed_request_ids:
            if dry_run:
                log_message(f"[dry-run] would retry failed request {request_id}")
                continue
            retry_status = retry_request_call(
                jellyseerr_url, jellyseerr_api_key, request_id
            )
            log_message(f"retried failed request {request_id} -> {retry_status}")
    elif failed_request_ids:
        log_message(
            "chain starting; deferring retry of failed requests until radarr is ready"
        )
