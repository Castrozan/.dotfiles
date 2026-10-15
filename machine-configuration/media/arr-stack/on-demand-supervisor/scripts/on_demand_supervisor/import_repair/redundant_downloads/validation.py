from dataclasses import dataclass
from pathlib import PurePosixPath

from import_repair.redundant_downloads.eligibility import (
    positive_identifier,
    redundant_reasons,
    scoped_path,
)

MAX_CANDIDATES = 200


@dataclass(frozen=True)
class RedundantEpisodeDownload:
    source_files: dict
    episode_files: dict


def candidate_source_path(record, candidate):
    path = scoped_path(candidate.get("path"), "/data/torrents")
    if path is None:
        return None
    output_path = PurePosixPath(record["outputPath"])
    if path != output_path and path.parent != output_path:
        return None
    return path


def candidate_identity_matches(record, candidate):
    return (
        candidate.get("downloadId", "").lower() == record["downloadId"].lower()
        and (candidate.get("series") or {}).get("id") == record["seriesId"]
        and positive_identifier(candidate.get("size"))
    )


def candidate_rejections_are_redundant(candidate):
    rejections = candidate.get("rejections") or []
    return redundant_reasons([item.get("reason") for item in rejections]) and all(
        item.get("type") == "permanent" for item in rejections
    )


def existing_episode_is_identified(episode, series_id):
    return (
        episode.get("seriesId") == series_id
        and episode.get("hasFile") is True
        and positive_identifier(episode.get("id"))
        and positive_identifier(episode.get("episodeFileId"))
    )


def candidate_episode_files(candidate, series_id):
    episodes = candidate.get("episodes", [])
    if not episodes:
        return None
    if not all(
        existing_episode_is_identified(episode, series_id) for episode in episodes
    ):
        return None
    return {episode["id"]: episode["episodeFileId"] for episode in episodes}


def candidate_metadata_is_redundant(record, candidate):
    return candidate_identity_matches(
        record, candidate
    ) and candidate_rejections_are_redundant(candidate)


def add_validated_candidate(record, candidate, download):
    path = candidate_source_path(record, candidate)
    if path is None or path in download.source_files:
        return False
    if not candidate_metadata_is_redundant(record, candidate):
        return False
    episodes = candidate_episode_files(candidate, record["seriesId"])
    if episodes is None:
        return False
    download.source_files[path] = candidate["size"]
    download.episode_files.update(episodes)
    return True


def validated_download(record, candidates):
    if not candidates or len(candidates) > MAX_CANDIDATES:
        return None
    download = RedundantEpisodeDownload({}, {})
    for candidate in candidates:
        if not add_validated_candidate(record, candidate, download):
            return None
    return download
