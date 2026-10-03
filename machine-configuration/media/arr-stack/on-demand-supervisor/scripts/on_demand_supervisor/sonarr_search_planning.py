def season_key(record):
    return record.get("seriesId"), record.get("seasonNumber")


def _is_complete_missing_season(statistics, missing_count):
    episode_count = _nonzero_season_statistic(statistics, "episodeCount")
    if not episode_count > 1:
        return False
    episode_file_count = _nonzero_season_statistic(statistics, "episodeFileCount")
    if episode_file_count != 0:
        return False
    if missing_count != episode_count:
        return False
    return True


def _nonzero_season_statistic(statistics, field_name):
    return statistics.get(field_name, 0) or 0


def complete_missing_season_keys(missing_records, series):
    missing_counts = {}
    for record in missing_records:
        key = season_key(record)
        missing_counts[key] = missing_counts.get(key, 0) + 1
    statistics_by_season = {
        (series_record.get("id"), season.get("seasonNumber")): season.get(
            "statistics", {}
        )
        for series_record in series
        for season in series_record.get("seasons", [])
    }
    complete_keys = set()
    for key, missing_count in missing_counts.items():
        statistics = statistics_by_season.get(key, {})
        if _is_complete_missing_season(statistics, missing_count):
            complete_keys.add(key)
    return complete_keys


def _queued_sonarr_item_ids(downloads):
    queued_series_ids = set()
    queued_episode_ids = set()
    for record in downloads:
        series_id = record.get("seriesId")
        if series_id is not None:
            queued_series_ids.add(series_id)
        episode_id = record.get("episodeId")
        if episode_id is not None:
            queued_episode_ids.add(episode_id)
    return queued_series_ids, queued_episode_ids


def _missing_season_targets(missing_records, complete_keys, queued_series_ids):
    season_targets = []
    seen_seasons = set()
    for record in missing_records:
        key = season_key(record)
        if key not in complete_keys:
            continue
        if key[0] in queued_series_ids:
            continue
        if key in seen_seasons:
            continue
        season_targets.append(key)
        seen_seasons.add(key)
    return season_targets


def _missing_episode_ids(missing_records, complete_keys, queued_episode_ids):
    return [
        record["id"]
        for record in missing_records
        if season_key(record) not in complete_keys
        and record.get("id") not in queued_episode_ids
    ]


def build_sonarr_search_plan(missing_records, series, downloads):
    complete_keys = complete_missing_season_keys(missing_records, series)
    queued_series_ids, queued_episode_ids = _queued_sonarr_item_ids(downloads)
    season_targets = _missing_season_targets(
        missing_records, complete_keys, queued_series_ids
    )
    episode_ids = _missing_episode_ids(
        missing_records, complete_keys, queued_episode_ids
    )
    return season_targets, episode_ids
