from urllib.parse import urlencode

TITLE_REJECTIONS = frozenset({"Unknown Movie", "Unknown Series", "Unknown Episode"})


def grabbed_identity(application, download_id, history):
    records = history.get("records", [])
    if history.get("totalRecords", len(records)) > len(records):
        return None
    identities = {
        (record.get("seriesId"), record.get("episodeId"))
        if application == "sonarr"
        else (record.get("movieId"),)
        for record in records
        if record.get("downloadId", "").lower() == download_id.lower()
        and record.get("eventType") == "grabbed"
    }
    if len(identities) != 1:
        return None
    identity = identities.pop()
    return identity if all(identity) else None


def reprocess_from_history(application, record, candidates, request):
    if len(candidates) != 1:
        return candidates
    candidate = candidates[0]
    reasons = {rejection.get("reason") for rejection in candidate.get("rejections", [])}
    if (
        not reasons
        or not reasons.issubset(TITLE_REJECTIONS)
        or candidate.get("path") != record.get("outputPath")
        or candidate.get("downloadId", "").lower() != record["downloadId"].lower()
    ):
        return candidates
    history = request(
        "history?" + urlencode({"downloadId": record["downloadId"], "pageSize": 100})
    )
    identity = grabbed_identity(application, record["downloadId"], history)
    if identity is None:
        return candidates
    kind = "series" if application == "sonarr" else "movie"
    media = request(f"{kind}/{identity[0]}")
    if not media.get("monitored"):
        return candidates
    proposed = {**candidate, kind + "Id": identity[0], kind: media}
    if application == "sonarr":
        episode = request(f"episode/{identity[1]}")
        if (
            episode.get("seriesId") != identity[0]
            or not episode.get("monitored")
            or episode.get("hasFile", True)
        ):
            return candidates
        proposed.update(episodeIds=[identity[1]], seasonNumber=episode["seasonNumber"])
    elif media.get("hasFile", True):
        return candidates
    return request("manualimport", [proposed])
