from functools import partial
import json
from pathlib import Path
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
from import_repair.redundant_downloads.selection import select_downloads
from missing_search_api import queued_records
from runtime_environment import log, read_arr_api_key_from_config_xml


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


def cleanup_queued_downloads(base_url, api_key, records, state_path, dry_run):
    for record in select_downloads(records, state_path, dry_run):
        try:
            remove_redundant_download(base_url, api_key, record, dry_run)
        except (OSError, ValueError, KeyError, TypeError, ParseError):
            log(
                f"redundant-download: verification failed for {record['downloadId']}; preserving"
            )


def maybe_cleanup_redundant_downloads(configuration, dry_run):
    state_file = configuration.get("state_file_path")
    if not state_file:
        return
    try:
        state_path = Path(state_file).with_name("redundant-download-cursor")
        api_key = read_arr_api_key_from_config_xml(configuration["sonarr_config_file"])
        base_url = configuration["sonarr_url"]
        records = queued_records(base_url, api_key)
        cleanup_queued_downloads(base_url, api_key, records, state_path, dry_run)
    except (OSError, ValueError, KeyError, TypeError, ParseError):
        log("redundant-download: maintenance unavailable; deferring")
