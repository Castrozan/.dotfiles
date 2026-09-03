def season_key(record):
    return record.get("seriesId"), record.get("seasonNumber")


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
        episode_count = statistics.get("episodeCount", 0) or 0
        episode_file_count = statistics.get("episodeFileCount", 0) or 0
        if (
            episode_count > 1
            and episode_file_count == 0
            and missing_count == episode_count
        ):
            complete_keys.add(key)
    return complete_keys


def build_sonarr_search_plan(missing_records, series, downloads):
    complete_keys = complete_missing_season_keys(missing_records, series)
    queued_series_ids = {
        record.get("seriesId")
        for record in downloads
        if record.get("seriesId") is not None
    }
    queued_episode_ids = {
        record.get("episodeId")
        for record in downloads
        if record.get("episodeId") is not None
    }
    season_targets = []
    seen_seasons = set()
    for record in missing_records:
        key = season_key(record)
        if (
            key in complete_keys
            and key[0] not in queued_series_ids
            and key not in seen_seasons
        ):
            season_targets.append(key)
            seen_seasons.add(key)
    episode_ids = [
        record["id"]
        for record in missing_records
        if season_key(record) not in complete_keys
        and record.get("id") not in queued_episode_ids
    ]
    return season_targets, episode_ids
