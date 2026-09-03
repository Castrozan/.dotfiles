from missing_search_api import (
    active_indexer_count,
    monitored_missing_records,
    queued_records,
    series_records,
    trigger_search,
)
from runtime_environment import log
from sonarr_search_planning import build_sonarr_search_plan

MISSING_SEARCH_ITEM_CAP = 200


def searchable_endpoint(endpoint, now_epoch):
    base_url, api_key = endpoint
    active_count = active_indexer_count(base_url, api_key, now_epoch)
    if active_count is None:
        log(f"missing-search sweep: {base_url} unreachable; deferring")
        return None
    if active_count <= 0:
        log(
            f"missing-search sweep: {base_url} reports 0 active indexers; "
            "deferring until they recover"
        )
        return None
    return base_url, api_key, active_count


def capped_missing_records(base_url, records):
    capped_records = records[:MISSING_SEARCH_ITEM_CAP]
    if len(records) > len(capped_records):
        log(
            f"missing-search sweep: {base_url} capping this run at "
            f"{MISSING_SEARCH_ITEM_CAP} of {len(records)} missing items; "
            "the rest follow on the next sweep"
        )
    return capped_records


def sweep_app(endpoint, command_name, payload_key, queue_id_field, now_epoch, dry_run):
    searchable = searchable_endpoint(endpoint, now_epoch)
    if searchable is None:
        return "deferred"
    base_url, api_key, active_count = searchable
    missing_records = monitored_missing_records(base_url, api_key)
    downloads = queued_records(base_url, api_key)
    if missing_records is None or downloads is None:
        log(f"missing-search sweep: {base_url} state unavailable; deferring")
        return "deferred"
    queued_item_ids = {record.get(queue_id_field) for record in downloads}
    searchable_records = [
        record
        for record in missing_records
        if record.get("id") is not None and record.get("id") not in queued_item_ids
    ]
    capped_item_ids = [
        record["id"] for record in capped_missing_records(base_url, searchable_records)
    ]
    if not capped_item_ids:
        return "swept"
    payload = {"name": command_name, payload_key: capped_item_ids}
    if not trigger_search(base_url, api_key, payload, len(capped_item_ids), dry_run):
        return "deferred"
    log(
        f"missing-search sweep: {base_url} sent {command_name} for "
        f"{len(capped_item_ids)} monitored-missing items with "
        f"{active_count} active indexers"
    )
    return "swept"


def sweep_sonarr(endpoint, now_epoch, dry_run):
    searchable = searchable_endpoint(endpoint, now_epoch)
    if searchable is None:
        return "deferred"
    base_url, api_key, active_count = searchable
    missing_records = monitored_missing_records(base_url, api_key)
    series = series_records(base_url, api_key)
    downloads = queued_records(base_url, api_key)
    if missing_records is None or series is None or downloads is None:
        log(f"missing-search sweep: {base_url} state unavailable; deferring")
        return "deferred"
    capped_records = capped_missing_records(base_url, missing_records)
    season_targets, episode_ids = build_sonarr_search_plan(
        capped_records, series, downloads
    )
    for series_id, season_number in season_targets:
        payload = {
            "name": "SeasonSearch",
            "seriesId": series_id,
            "seasonNumber": season_number,
        }
        if not trigger_search(base_url, api_key, payload, 1, dry_run):
            return "deferred"
    if episode_ids:
        payload = {"name": "EpisodeSearch", "episodeIds": episode_ids}
        if not trigger_search(base_url, api_key, payload, len(episode_ids), dry_run):
            return "deferred"
    if season_targets or episode_ids:
        log(
            f"missing-search sweep: {base_url} sent SeasonSearch for "
            f"{len(season_targets)} complete missing seasons and EpisodeSearch "
            f"for {len(episode_ids)} monitored-missing items with "
            f"{active_count} active indexers"
        )
    return "swept"


def run_missing_search_sweep(radarr_endpoint, sonarr_endpoint, now_epoch, dry_run):
    outcomes = [
        sweep_app(
            radarr_endpoint, "MoviesSearch", "movieIds", "movieId", now_epoch, dry_run
        ),
        sweep_sonarr(sonarr_endpoint, now_epoch, dry_run),
    ]
    return "swept" in outcomes
