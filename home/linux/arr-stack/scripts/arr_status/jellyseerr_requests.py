import arr_http

REQUEST_STATUS_PENDING_APPROVAL = 1
REQUEST_STATUS_DECLINED = 3
MEDIA_STATUS_PARTIALLY_AVAILABLE = 4
MEDIA_STATUS_AVAILABLE = 5

JELLYSEERR_REQUEST_PAGE_SIZE = 100


def fetch_requests(base_url, api_key):
    result = arr_http.get_json(
        base_url,
        api_key,
        f"/api/v1/request?take={JELLYSEERR_REQUEST_PAGE_SIZE}&sort=added",
    )
    return (result or {}).get("results", [])


def resolve_media_title(base_url, api_key, media_type, tmdb_id):
    if media_type == "movie":
        detail = arr_http.get_json(base_url, api_key, f"/api/v1/movie/{tmdb_id}")
        return (detail or {}).get("title"), year_from_date(
            (detail or {}).get("releaseDate")
        )
    detail = arr_http.get_json(base_url, api_key, f"/api/v1/tv/{tmdb_id}")
    return (detail or {}).get("name"), year_from_date(
        (detail or {}).get("firstAirDate")
    )


def year_from_date(date_text):
    if not date_text or len(date_text) < 4:
        return None
    return date_text[:4]


def request_lifecycle_stage(request_object):
    request_status = request_object.get("status")
    media_status = request_object.get("media", {}).get("status")
    if request_status == REQUEST_STATUS_PENDING_APPROVAL:
        return "pending-approval"
    if request_status == REQUEST_STATUS_DECLINED:
        return "declined"
    if media_status == MEDIA_STATUS_AVAILABLE:
        return "available"
    if media_status == MEDIA_STATUS_PARTIALLY_AVAILABLE:
        return "partial"
    return "processing"
