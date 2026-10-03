def download_candidate_metadata_matches(record, candidate):
    if candidate.get("rejections"):
        return False
    if not candidate.get("quality"):
        return False
    if not candidate.get("languages"):
        return False
    if candidate.get("downloadId", "").lower() != record["downloadId"].lower():
        return False
    return True


def download_candidate_path_matches(path, output_path):
    if str(path) != output_path:
        return False
    if not path.is_relative_to("/data/torrents"):
        return False
    if ".." in path.parts:
        return False
    return True


def missing_episode_is_importable(episode, series_id):
    if not episode.get("id"):
        return False
    if episode.get("seriesId") != series_id:
        return False
    if not episode.get("monitored"):
        return False
    if episode.get("hasFile", True):
        return False
    return True


def _download_is_completed_import_blocked(record):
    if record.get("status") != "completed":
        return False
    if record.get("trackedDownloadState") != "importBlocked":
        return False
    if record.get("sizeleft") != 0:
        return False
    return True


def blocked_download_record_is_repairable(record):
    if not record.get("downloadId"):
        return False
    if not _download_is_completed_import_blocked(record):
        return False
    if not record.get("outputPath"):
        return False
    return True


def repairable_download_records(records):
    repairable_records = {}
    for record in records:
        if not blocked_download_record_is_repairable(record):
            continue
        repairable_records[record["downloadId"]] = record
    return repairable_records


def manual_import_is_active(commands):
    for command in commands:
        if command.get("name") != "ManualImport":
            continue
        if command.get("status") in ("queued", "started"):
            return True
    return False


def media_is_importable(media):
    if not media.get("id"):
        return False
    if not media.get("monitored"):
        return False
    return True
