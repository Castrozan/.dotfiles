from urllib.parse import urlencode

TITLE_REJECTIONS = frozenset({"Unknown Movie", "Unknown Series", "Unknown Episode"})


def grabbed_identity(application, download_id, history):
    records = history.get("records", [])
    if history.get("totalRecords", len(records)) > len(records):
        return None
    identities = _grabbed_identities(application, download_id, records)
    if len(identities) != 1:
        return None
    identity = identities.pop()
    return identity if all(identity) else None


def _grabbed_identities(application, download_id, records):
    return {
        _record_identity(application, record)
        for record in records
        if record.get("downloadId", "").lower() == download_id.lower()
        and record.get("eventType") == "grabbed"
    }


def _record_identity(application, record):
    if application == "sonarr":
        return record.get("seriesId"), record.get("episodeId")
    return (record.get("movieId"),)


def _candidate_rejections_are_title_only(candidate, record, reasons):
    if not reasons:
        return False
    if not reasons.issubset(TITLE_REJECTIONS):
        return False
    if candidate.get("path") != record.get("outputPath"):
        return False
    if candidate.get("downloadId", "").lower() != record["downloadId"].lower():
        return False
    return True


def _episode_can_be_reprocessed(episode, series_id):
    if episode.get("seriesId") != series_id:
        return False
    if not episode.get("monitored"):
        return False
    if episode.get("hasFile", True):
        return False
    return True


def _resolve_grabbed_media(application, record, request):
    identity = grabbed_identity(
        application,
        record["downloadId"],
        request(
            "history?"
            + urlencode({"downloadId": record["downloadId"], "pageSize": 100})
        ),
    )
    if identity is None:
        return None
    kind = "series" if application == "sonarr" else "movie"
    media = request(f"{kind}/{identity[0]}")
    if not media.get("monitored"):
        return None
    return identity, kind, media


def _build_reprocessed_candidate(
    application, candidate, identity, kind, media, request
):
    proposed = {**candidate, kind + "Id": identity[0], kind: media}
    if application == "sonarr":
        episode = request(f"episode/{identity[1]}")
        if not _episode_can_be_reprocessed(episode, identity[0]):
            return None
        proposed.update(episodeIds=[identity[1]], seasonNumber=episode["seasonNumber"])
    elif media.get("hasFile", True):
        return None
    return proposed


def reprocess_from_history(application, record, candidates, request):
    if len(candidates) != 1:
        return candidates
    candidate = candidates[0]
    reasons = {rejection.get("reason") for rejection in candidate.get("rejections", [])}
    if not _candidate_rejections_are_title_only(candidate, record, reasons):
        return candidates
    resolved_media = _resolve_grabbed_media(application, record, request)
    if resolved_media is None:
        return candidates
    identity, kind, media = resolved_media
    proposed = _build_reprocessed_candidate(
        application, candidate, identity, kind, media, request
    )
    if proposed is None:
        return candidates
    return request("manualimport", [proposed])
