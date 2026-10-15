import re
from dataclasses import dataclass
from pathlib import PurePosixPath

MAX_CANDIDATES = 200
NOT_AN_UPGRADE = "Not an upgrade for existing episode file(s)."


@dataclass(frozen=True)
class RedundantEpisodeDownload:
    source_files: dict
    episode_files: dict


def scoped_path(value, root):
    if not isinstance(value, str) or not value:
        return None
    path = PurePosixPath(value)
    if (
        ".." in path.parts
        or not path.is_relative_to(root)
        or path == PurePosixPath(root)
    ):
        return None
    return path


def positive_identifier(value):
    return type(value) is int and value > 0


def redundant_reasons(reasons):
    return bool(reasons) and all(
        isinstance(reason, str) and reason.startswith(NOT_AN_UPGRADE)
        for reason in reasons
    )


def eligible_record(record):
    reasons = [
        message
        for status in record.get("statusMessages", [])
        for message in status.get("messages", [])
    ]
    return (
        positive_identifier(record.get("id"))
        and positive_identifier(record.get("seriesId"))
        and re.fullmatch(
            r"[a-fA-F0-9]{40}|[a-fA-F0-9]{64}", record.get("downloadId") or ""
        )
        and record.get("status") == "completed"
        and record.get("trackedDownloadState") == "importBlocked"
        and record.get("sizeleft") == 0
        and scoped_path(record.get("outputPath"), "/data/torrents") is not None
        and redundant_reasons(reasons)
    )


def validated_download(record, candidates):
    if not candidates or len(candidates) > MAX_CANDIDATES:
        return None
    output_path = PurePosixPath(record["outputPath"])
    source_files = {}
    episode_files = {}
    for candidate in candidates:
        path = scoped_path(candidate.get("path"), "/data/torrents")
        if path is None or (path != output_path and path.parent != output_path):
            return None
        if path in source_files or not positive_identifier(candidate.get("size")):
            return None
        if candidate.get("downloadId", "").lower() != record["downloadId"].lower():
            return None
        if (candidate.get("series") or {}).get("id") != record["seriesId"]:
            return None
        rejections = candidate.get("rejections") or []
        if not redundant_reasons([item.get("reason") for item in rejections]):
            return None
        if any(item.get("type") != "permanent" for item in rejections):
            return None
        episodes = candidate.get("episodes") or []
        if not episodes:
            return None
        for episode in episodes:
            if (
                episode.get("seriesId") != record["seriesId"]
                or episode.get("hasFile") is not True
                or not positive_identifier(episode.get("id"))
                or not positive_identifier(episode.get("episodeFileId"))
            ):
                return None
            episode_files[episode["id"]] = episode["episodeFileId"]
        source_files[path] = candidate["size"]
    return RedundantEpisodeDownload(source_files, episode_files)
