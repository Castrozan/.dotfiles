import json
from pathlib import PurePosixPath
from urllib.parse import urlencode
from xml.etree.ElementTree import ParseError

from http_client import http_request
from import_repair.candidate_validation import manual_import_is_active
from missing_search_api import queued_records
from import_repair.redundant_downloads.validation import (
    eligible_record,
    positive_identifier,
    scoped_path,
    validated_download,
)
from runtime_environment import log, read_arr_api_key_from_config_xml

MAX_DOWNLOADS_PER_TICK = 2
MAX_LIBRARY_DIRECTORIES = 4


def read_json(base_url, api_key, path):
    status, body = http_request(
        "GET", base_url + "/api/v3/" + path, {"X-Api-Key": api_key}, timeout_seconds=5
    )
    if not 200 <= status < 300:
        raise ValueError(f"Sonarr returned HTTP {status}")
    return json.loads(body)


def directory_contents(read, directory):
    return read(
        "filesystem?"
        + urlencode({"path": str(directory) + "/", "includeFiles": "true"})
    )


def source_files_verified(record, download, read):
    output_path = PurePosixPath(record["outputPath"])
    single_file = set(download.source_files) == {output_path}
    directory = output_path.parent if single_file else output_path
    contents = directory_contents(read, directory)
    files = {PurePosixPath(item["path"]): item for item in contents.get("files", [])}
    if not single_file and (
        contents.get("directories") or set(files) != set(download.source_files)
    ):
        return False
    return all(
        files.get(path, {}).get("type") == "file" and files[path].get("size") == size
        for path, size in download.source_files.items()
    )


def library_files_verified(record, download, read):
    query = urlencode({"seriesId": record["seriesId"]})
    episodes = {item["id"]: item for item in read("episode?" + query)}
    files = {item["id"]: item for item in read("episodefile?" + query)}
    library_files = {}
    for episode_id, file_id in download.episode_files.items():
        episode = episodes.get(episode_id, {})
        if (
            episode.get("seriesId") != record["seriesId"]
            or episode.get("hasFile") is not True
            or episode.get("episodeFileId") != file_id
        ):
            return False
        file = files.get(file_id, {})
        path = scoped_path(file.get("path"), "/data/media/tv")
        if (
            path is None
            or file.get("seriesId") != record["seriesId"]
            or not positive_identifier(file.get("size"))
        ):
            return False
        library_files[path] = file["size"]
    directories = {path.parent for path in library_files}
    if len(directories) > MAX_LIBRARY_DIRECTORIES:
        return False
    actual_files = {}
    for directory in sorted(directories):
        actual_files.update(
            (PurePosixPath(item["path"]), item)
            for item in directory_contents(read, directory).get("files", [])
        )
    return all(
        actual_files.get(path, {}).get("type") == "file"
        and actual_files[path].get("size") == size
        for path, size in library_files.items()
    )


def remove_redundant_download(base_url, api_key, record, dry_run):
    if not eligible_record(record):
        return False
    read = lambda path: read_json(base_url, api_key, path)
    if manual_import_is_active(read("command")):
        return False
    candidates = read(
        "manualimport?"
        + urlencode(
            {
                "downloadId": record["downloadId"],
                "folder": record["outputPath"],
                "filterExistingFiles": "false",
            }
        )
    )
    download = validated_download(record, candidates)
    if download is None or not source_files_verified(record, download, read):
        return False
    if not library_files_verified(record, download, read):
        return False
    if dry_run:
        log(f"redundant-download: would remove {record['downloadId']}")
        return False
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
        f"redundant-download: removed {record['downloadId']} after verifying {len(download.episode_files)} library episodes"
    )
    return True


def maybe_cleanup_redundant_downloads(configuration, now_epoch, dry_run):
    try:
        api_key = read_arr_api_key_from_config_xml(configuration["sonarr_config_file"])
        base_url = configuration["sonarr_url"]
        records = queued_records(base_url, api_key)
        if records is None:
            return
    except (OSError, ValueError, ParseError):
        log("redundant-download: Sonarr unavailable; deferring")
        return
    downloads = {
        record["downloadId"].lower(): record
        for record in records
        if eligible_record(record)
    }
    identities = sorted(downloads)
    if not identities:
        return
    offset = int(now_epoch // 60) * MAX_DOWNLOADS_PER_TICK % len(identities)
    identities = identities[offset:] + identities[:offset]
    for identity in identities[:MAX_DOWNLOADS_PER_TICK]:
        try:
            remove_redundant_download(base_url, api_key, downloads[identity], dry_run)
        except (OSError, ValueError, KeyError, TypeError, ParseError):
            log(f"redundant-download: verification failed for {identity}; preserving")
