import json
import urllib.error

from http_client import http_request
from runtime_environment import log, parse_iso8601_to_epoch

MISSING_SEARCH_ITEM_CAP = 200

UNREACHABLE_ERRORS = (urllib.error.URLError, OSError, TimeoutError)


def active_indexer_count(base_url, api_key, now_epoch):
    headers = {"X-Api-Key": api_key}
    try:
        indexer_status_code, indexer_body = http_request(
            "GET", f"{base_url}/api/v3/indexer", headers
        )
        if indexer_status_code != 200:
            return None
        searchable_indexer_ids = {
            indexer.get("id")
            for indexer in json.loads(indexer_body)
            if indexer.get("enableAutomaticSearch")
        }
        if not searchable_indexer_ids:
            return 0
        status_code, status_body = http_request(
            "GET", f"{base_url}/api/v3/indexerstatus", headers
        )
    except UNREACHABLE_ERRORS:
        return None
    disabled_indexer_ids = set()
    if status_code == 200:
        for entry in json.loads(status_body):
            disabled_till = entry.get("disabledTill")
            if disabled_till and parse_iso8601_to_epoch(disabled_till) > now_epoch:
                disabled_indexer_ids.add(entry.get("indexerId"))
    return len(searchable_indexer_ids - disabled_indexer_ids)


def monitored_missing_item_ids(base_url, api_key):
    try:
        status_code, body = http_request(
            "GET",
            f"{base_url}/api/v3/wanted/missing?pageSize=1000&monitored=true",
            {"X-Api-Key": api_key},
        )
    except UNREACHABLE_ERRORS:
        return []
    if status_code != 200:
        return []
    return [
        record.get("id")
        for record in json.loads(body).get("records", [])
        if record.get("id") is not None
    ]


def queued_item_ids(base_url, api_key, queue_id_field):
    try:
        status_code, body = http_request(
            "GET", f"{base_url}/api/v3/queue?pageSize=1000", {"X-Api-Key": api_key}
        )
    except UNREACHABLE_ERRORS:
        return set()
    if status_code != 200:
        return set()
    return {
        record.get(queue_id_field) for record in json.loads(body).get("records", [])
    }


def trigger_missing_search(
    base_url, api_key, command_name, payload_key, item_ids, dry_run
):
    if dry_run:
        log(
            f"[dry-run] would send {command_name} for {len(item_ids)} items to {base_url}"
        )
        return True
    try:
        http_request(
            "POST",
            f"{base_url}/api/v3/command",
            {"X-Api-Key": api_key, "Content-Type": "application/json"},
            body=json.dumps({"name": command_name, payload_key: item_ids}),
        )
    except UNREACHABLE_ERRORS:
        log(
            f"missing-search sweep: {base_url} unreachable while sending "
            f"{command_name}; deferring"
        )
        return False
    return True


def sweep_app(endpoint, command_name, payload_key, queue_id_field, now_epoch, dry_run):
    base_url, api_key = endpoint
    active_count = active_indexer_count(base_url, api_key, now_epoch)
    if active_count is None:
        log(f"missing-search sweep: {base_url} unreachable; deferring")
        return "deferred"
    if active_count <= 0:
        log(
            f"missing-search sweep: {base_url} reports 0 active indexers; "
            "deferring until they recover"
        )
        return "deferred"
    missing_item_ids = monitored_missing_item_ids(base_url, api_key)
    if not missing_item_ids:
        return "swept"
    already_queued_item_ids = queued_item_ids(base_url, api_key, queue_id_field)
    searchable_item_ids = [
        item_id
        for item_id in missing_item_ids
        if item_id not in already_queued_item_ids
    ]
    if not searchable_item_ids:
        return "swept"
    capped_item_ids = searchable_item_ids[:MISSING_SEARCH_ITEM_CAP]
    if len(searchable_item_ids) > len(capped_item_ids):
        log(
            f"missing-search sweep: {base_url} capping this run at "
            f"{MISSING_SEARCH_ITEM_CAP} of {len(searchable_item_ids)} missing items; "
            "the rest follow on the next sweep"
        )
    if not trigger_missing_search(
        base_url, api_key, command_name, payload_key, capped_item_ids, dry_run
    ):
        return "deferred"
    log(
        f"missing-search sweep: {base_url} sent {command_name} for "
        f"{len(capped_item_ids)} monitored-missing items with "
        f"{active_count} active indexers"
    )
    return "swept"


def run_missing_search_sweep(radarr_endpoint, sonarr_endpoint, now_epoch, dry_run):
    outcomes = [
        sweep_app(
            radarr_endpoint, "MoviesSearch", "movieIds", "movieId", now_epoch, dry_run
        ),
        sweep_app(
            sonarr_endpoint,
            "EpisodeSearch",
            "episodeIds",
            "episodeId",
            now_epoch,
            dry_run,
        ),
    ]
    return "swept" in outcomes
