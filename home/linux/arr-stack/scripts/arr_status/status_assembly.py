import urllib.error
from dataclasses import dataclass

import arr_queue
import jellyseerr_requests


@dataclass
class ArrSnapshot:
    reachable: bool
    records: list
    id_by_external_id: dict


@dataclass
class MediaStatusLine:
    title: str
    year: str | None
    media_type: str
    requested_by: str
    stage: str
    progress: dict | None
    arr_reachable: bool


def snapshot_radarr(endpoint):
    return build_snapshot(endpoint, arr_queue.build_radarr_movie_index)


def snapshot_sonarr(endpoint):
    return build_snapshot(endpoint, arr_queue.build_sonarr_series_index)


def build_snapshot(endpoint, build_index):
    if endpoint is None:
        return ArrSnapshot(reachable=False, records=[], id_by_external_id={})
    try:
        records = arr_queue.fetch_queue_records(endpoint)
        id_by_external_id = build_index(endpoint)
    except urllib.error.URLError:
        return ArrSnapshot(reachable=False, records=[], id_by_external_id={})
    return ArrSnapshot(
        reachable=True, records=records, id_by_external_id=id_by_external_id
    )


def progress_from_snapshot(snapshot, external_id, record_id_field):
    if not snapshot.reachable:
        return None
    arr_id = snapshot.id_by_external_id.get(external_id)
    if arr_id is None:
        return None
    matching_records = [
        record for record in snapshot.records if record.get(record_id_field) == arr_id
    ]
    return arr_queue.download_progress_for_records(matching_records)


def progress_for_request(request_object, radarr_snapshot, sonarr_snapshot):
    media = request_object.get("media", {})
    if media.get("mediaType") == "movie":
        return progress_from_snapshot(radarr_snapshot, media.get("tmdbId"), "movieId")
    return progress_from_snapshot(sonarr_snapshot, media.get("tvdbId"), "seriesId")


def build_status_line(
    jellyseerr_base_url,
    jellyseerr_api_key,
    request_object,
    radarr_snapshot,
    sonarr_snapshot,
):
    media = request_object.get("media", {})
    title, year = jellyseerr_requests.resolve_media_title(
        jellyseerr_base_url,
        jellyseerr_api_key,
        media.get("mediaType"),
        media.get("tmdbId"),
    )
    return assemble_status_line(
        request_object, title, year, radarr_snapshot, sonarr_snapshot
    )


def build_status_line_tolerating_title_failure(
    jellyseerr_base_url,
    jellyseerr_api_key,
    request_object,
    radarr_snapshot,
    sonarr_snapshot,
):
    media = request_object.get("media", {})
    try:
        title, year = jellyseerr_requests.resolve_media_title(
            jellyseerr_base_url,
            jellyseerr_api_key,
            media.get("mediaType"),
            media.get("tmdbId"),
        )
    except urllib.error.URLError:
        title, year = None, None
    return assemble_status_line(
        request_object, title, year, radarr_snapshot, sonarr_snapshot
    )


def assemble_status_line(request_object, title, year, radarr_snapshot, sonarr_snapshot):
    media = request_object.get("media", {})
    media_type = media.get("mediaType")
    relevant_snapshot = radarr_snapshot if media_type == "movie" else sonarr_snapshot
    return MediaStatusLine(
        title=title or f"tmdb:{media.get('tmdbId')}",
        year=year,
        media_type=media_type,
        requested_by=(request_object.get("requestedBy") or {}).get("displayName", "?"),
        stage=jellyseerr_requests.request_lifecycle_stage(request_object),
        progress=progress_for_request(request_object, radarr_snapshot, sonarr_snapshot),
        arr_reachable=relevant_snapshot.reachable,
    )
