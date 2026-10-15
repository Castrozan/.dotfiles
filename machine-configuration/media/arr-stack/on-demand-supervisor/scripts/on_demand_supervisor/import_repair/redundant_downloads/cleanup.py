from functools import partial
import json
from urllib.parse import urlencode
from xml.etree.ElementTree import ParseError

from http_client import http_request
from import_repair.candidate_validation import manual_import_is_active
from import_repair.redundant_downloads.eligibility import eligible_record
from import_repair.redundant_downloads.filesystem import (
    library_files_verified,
    source_files_verified,
)
from import_repair.redundant_downloads.validation import validated_download
from missing_search_api import queued_records
from runtime_environment import log, read_arr_api_key_from_config_xml

MAX_DOWNLOADS_PER_TICK = 2


def read_json(base_url, api_key, path):
    status, body = http_request(
        "GET", base_url + "/api/v3/" + path, {"X-Api-Key": api_key}, timeout_seconds=5
    )
    if not 200 <= status < 300:
        raise ValueError(f"Sonarr returned HTTP {status}")
    return json.loads(body)


def manual_import_candidates(record, read):
    return read(
        "manualimport?"
        + urlencode(
            {
                "downloadId": record["downloadId"],
                "folder": record["outputPath"],
                "filterExistingFiles": "false",
            }
        )
    )


def download_files_verified(record, download, read):
    return (
        download is not None
        and source_files_verified(record, download, read)
        and library_files_verified(record, download, read)
    )


def remove_from_queue(base_url, api_key, record, episode_count):
    query = urlencode(
        {"removeFromClient": "true", "blocklist": "false", "skipRedownload": "true"}
    )
    status, _ = http_request(
        "DELETE",
        base_url + f"/api/v3/queue/{record['id']}?{query}",
        {"X-Api-Key": api_key},
        timeout_seconds=5,
    )
    if not 200 <= status < 300:
        raise ValueError(f"Sonarr removal returned HTTP {status}")
    log(
        f"redundant-download: removed {record['downloadId']} after verifying {episode_count} library episodes"
    )
    return True


def remove_redundant_download(base_url, api_key, record, dry_run):
    if not eligible_record(record):
        return False
    read = partial(read_json, base_url, api_key)
    if manual_import_is_active(read("command")):
        return False
    download = validated_download(record, manual_import_candidates(record, read))
    if not download_files_verified(record, download, read):
        return False
    if dry_run:
        log(f"redundant-download: would remove {record['downloadId']}")
        return False
    return remove_from_queue(base_url, api_key, record, len(download.episode_files))


def unique_redundant_downloads(records):
    return {
        record["downloadId"].lower(): record
        for record in records
        if eligible_record(record)
    }


def rotating_downloads(records, now_epoch):
    downloads = unique_redundant_downloads(records or [])
    identities = sorted(downloads)
    if not identities:
        return []
    offset = int(now_epoch // 60) * MAX_DOWNLOADS_PER_TICK % len(identities)
    identities = identities[offset:] + identities[:offset]
    return [downloads[identity] for identity in identities[:MAX_DOWNLOADS_PER_TICK]]


def cleanup_queued_downloads(base_url, api_key, records, now_epoch, dry_run):
    for record in rotating_downloads(records, now_epoch):
        try:
            remove_redundant_download(base_url, api_key, record, dry_run)
        except (OSError, ValueError, KeyError, TypeError, ParseError):
            log(
                f"redundant-download: verification failed for {record['downloadId']}; preserving"
            )


def maybe_cleanup_redundant_downloads(configuration, now_epoch, dry_run):
    try:
        api_key = read_arr_api_key_from_config_xml(configuration["sonarr_config_file"])
        base_url = configuration["sonarr_url"]
        records = queued_records(base_url, api_key)
        cleanup_queued_downloads(base_url, api_key, records, now_epoch, dry_run)
    except (OSError, ValueError, KeyError, TypeError, ParseError):
        log("redundant-download: Sonarr unavailable; deferring")
