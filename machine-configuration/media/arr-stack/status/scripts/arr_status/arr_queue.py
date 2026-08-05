import arr_http

ARR_QUEUE_PAGE_SIZE = 200


def fetch_queue_records(endpoint):
    result = arr_http.get_json(
        endpoint.base_url,
        endpoint.api_key,
        f"/api/v3/queue?pageSize={ARR_QUEUE_PAGE_SIZE}",
    )
    return (result or {}).get("records", [])


def build_radarr_movie_index(endpoint):
    movies = (
        arr_http.get_json(endpoint.base_url, endpoint.api_key, "/api/v3/movie") or []
    )
    return {movie.get("tmdbId"): movie.get("id") for movie in movies}


def build_sonarr_series_index(endpoint):
    series = (
        arr_http.get_json(endpoint.base_url, endpoint.api_key, "/api/v3/series") or []
    )
    return {item.get("tvdbId"): item.get("id") for item in series}


def download_progress_for_records(records):
    total_size = sum(record.get("size", 0) or 0 for record in records)
    total_size_left = sum(record.get("sizeleft", 0) or 0 for record in records)
    if total_size <= 0:
        return None
    downloaded_percent = round((total_size - total_size_left) / total_size * 100)
    return {
        "percent": downloaded_percent,
        "time_left": bottleneck_time_left(records),
        "record_count": len(records),
    }


def bottleneck_time_left(records):
    records_with_time_left = [record for record in records if record.get("timeleft")]
    if not records_with_time_left:
        return None
    slowest_record = max(
        records_with_time_left, key=lambda record: record.get("sizeleft", 0) or 0
    )
    return slowest_record.get("timeleft")
