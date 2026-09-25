import json
from pathlib import Path, PurePosixPath
from urllib.parse import urlencode
from xml.etree.ElementTree import ParseError

from download_chain_control import read_last_active_epoch, write_last_active_epoch
from http_client import http_request
from import_repair.history import reprocess_from_history
from runtime_environment import log, read_arr_api_key_from_config_xml

REPAIR_INTERVAL_SECONDS = 900
MAX_DOWNLOADS_PER_APPLICATION = 2


def request_json(base_url, api_key, path, payload=None):
    status, body = http_request(
        "GET" if payload is None else "POST",
        base_url + "/api/v3/" + path,
        {"X-Api-Key": api_key, "Content-Type": "application/json"},
        timeout_seconds=5,
        body=None if payload is None else json.dumps(payload),
    )
    if not 200 <= status < 300:
        raise ValueError(f"ARR returned HTTP {status}")
    return json.loads(body)


def matches_download(record, candidate):
    path = PurePosixPath(candidate.get("path", ""))
    if (
        candidate.get("rejections")
        or not candidate.get("quality")
        or not candidate.get("languages")
        or candidate.get("downloadId", "").lower() != record["downloadId"].lower()
        or str(path) != record.get("outputPath")
        or not path.is_relative_to("/data/torrents")
        or ".." in path.parts
    ):
        return False
    return True


def missing_episode(candidate, series_id):
    episodes = candidate.get("episodes") or []
    if len(episodes) != 1:
        return None
    episode = episodes[0]
    if (
        not episode.get("id")
        or episode.get("seriesId") != series_id
        or not episode.get("monitored")
        or episode.get("hasFile", True)
    ):
        return None
    return episode["id"]


def import_file(application, record, candidates):
    if len(candidates) != 1 or not matches_download(record, candidates[0]):
        return None
    candidate = candidates[0]
    identity = "series" if application == "sonarr" else "movie"
    media = candidate.get(identity) or {}
    if not media.get("id") or not media.get("monitored"):
        return None
    result = {
        "path": candidate["path"],
        identity + "Id": media["id"],
        "quality": candidate["quality"],
        "languages": candidate["languages"],
        "downloadId": record["downloadId"],
        "releaseGroup": candidate.get("releaseGroup", ""),
    }
    if application == "sonarr":
        episode_id = missing_episode(candidate, media["id"])
        if episode_id is None:
            return None
        result["episodeIds"] = [episode_id]
    elif media.get("hasFile", True):
        return None
    return result


def repair_application(application, base_url, api_key, now_epoch, dry_run):
    queue = request_json(
        base_url,
        api_key,
        "queue?"
        + urlencode(
            {
                "pageSize": 1000,
                "includeUnknownSeriesItems": "true",
                "includeUnknownMovieItems": "true",
            }
        ),
    )
    records = {
        record["downloadId"]: record
        for record in queue.get("records", [])
        if record.get("downloadId")
        and record.get("status") == "completed"
        and record.get("trackedDownloadState") == "importBlocked"
        and record.get("sizeleft") == 0
        and record.get("outputPath")
    }
    identities = sorted(records)
    if not identities:
        return
    commands = request_json(base_url, api_key, "command")
    if any(
        command.get("name") == "ManualImport"
        and command.get("status") in ("queued", "started")
        for command in commands
    ):
        return
    offset = (
        int(now_epoch // REPAIR_INTERVAL_SECONDS) * MAX_DOWNLOADS_PER_APPLICATION
    ) % len(identities)
    identities = identities[offset:] + identities[:offset]
    for identity in identities[:MAX_DOWNLOADS_PER_APPLICATION]:
        record = records[identity]
        candidates = request_json(
            base_url,
            api_key,
            "manualimport?"
            + urlencode(
                {
                    "downloadId": identity,
                    "folder": record["outputPath"],
                    "filterExistingFiles": "true",
                }
            ),
        )
        selected = import_file(application, record, candidates)
        if selected is None:
            candidates = reprocess_from_history(
                application,
                record,
                candidates,
                lambda path, payload=None: request_json(
                    base_url, api_key, path, payload
                ),
            )
            selected = import_file(application, record, candidates)
        if selected is None:
            continue
        if dry_run:
            log(f"import-repair: would import {application} download {identity}")
            continue
        command = request_json(
            base_url,
            api_key,
            "command",
            {"name": "ManualImport", "importMode": "copy", "files": [selected]},
        )
        log(
            f"import-repair: {application} command {command.get('id')} submitted for {identity}"
        )


def maybe_repair_blocked_imports(configuration, now_epoch, dry_run):
    state_file = configuration.get("state_file_path")
    if not state_file:
        return
    state_path = str(Path(state_file).with_name("import-repair-epoch"))
    try:
        last_attempt = read_last_active_epoch(state_path)
        if (
            last_attempt is not None
            and now_epoch - last_attempt < REPAIR_INTERVAL_SECONDS
        ):
            return
        if not dry_run:
            write_last_active_epoch(state_path, now_epoch)
    except OSError:
        log("import-repair: state unavailable; deferring")
        return
    for application in ("radarr", "sonarr"):
        try:
            api_key = read_arr_api_key_from_config_xml(
                configuration[f"{application}_config_file"]
            )
            repair_application(
                application,
                configuration[f"{application}_url"],
                api_key,
                now_epoch,
                dry_run,
            )
        except (OSError, ValueError, ParseError, TimeoutError):
            log(f"import-repair: {application} unavailable; deferring")
