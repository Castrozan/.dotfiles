from bisect import bisect_right
from pathlib import Path

from import_repair.redundant_downloads.eligibility import (
    eligible_record,
    torrent_identity_is_known,
)

MAX_DOWNLOADS_PER_TICK = 2


def unique_redundant_downloads(records):
    return {
        record["downloadId"].lower(): record
        for record in records
        if eligible_record(record)
    }


def read_cursor(state_path):
    try:
        with Path(state_path).open(encoding="utf-8") as handle:
            cursor = handle.read(65).strip().lower()
    except FileNotFoundError:
        return ""
    return cursor if torrent_identity_is_known(cursor) else ""


def rotating_identities(identities, cursor):
    offset = bisect_right(identities, cursor)
    return (identities[offset:] + identities[:offset])[:MAX_DOWNLOADS_PER_TICK]


def select_downloads(records, state_path, dry_run):
    downloads = unique_redundant_downloads(records or [])
    if not downloads:
        return []
    identities = rotating_identities(sorted(downloads), read_cursor(state_path))
    if not dry_run:
        Path(state_path).write_text(identities[-1] + "\n", encoding="utf-8")
    return [downloads[identity] for identity in identities]
