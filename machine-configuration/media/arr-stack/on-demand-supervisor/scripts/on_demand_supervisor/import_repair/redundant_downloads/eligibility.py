import re
from pathlib import PurePosixPath

from import_repair.candidate_validation import blocked_download_record_is_repairable

NOT_AN_UPGRADE = "Not an upgrade for existing episode file(s)."


def path_is_scoped(path, root):
    return (
        ".." not in path.parts
        and path.is_relative_to(root)
        and path != PurePosixPath(root)
    )


def scoped_path(value, root):
    if not isinstance(value, str) or not value:
        return None
    path = PurePosixPath(value)
    return path if path_is_scoped(path, root) else None


def positive_identifier(value):
    return type(value) is int and value > 0


def torrent_identity_is_known(value):
    return (
        isinstance(value, str)
        and re.fullmatch(r"[a-fA-F0-9]{40}|[a-fA-F0-9]{64}", value) is not None
    )


def record_identity_is_known(record):
    return (
        positive_identifier(record.get("id"))
        and positive_identifier(record.get("seriesId"))
        and torrent_identity_is_known(record.get("downloadId"))
    )


def redundant_reasons(reasons):
    return bool(reasons) and all(
        isinstance(reason, str) and reason.startswith(NOT_AN_UPGRADE)
        for reason in reasons
    )


def record_reasons(record):
    return [
        message
        for status in record.get("statusMessages", [])
        for message in status.get("messages", [])
    ]


def eligible_record(record):
    return (
        record_identity_is_known(record)
        and blocked_download_record_is_repairable(record)
        and scoped_path(record.get("outputPath"), "/data/torrents") is not None
        and redundant_reasons(record_reasons(record))
    )
