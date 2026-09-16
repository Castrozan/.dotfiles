from __future__ import annotations

import os
import re
from datetime import datetime, timedelta
from pathlib import Path

PROCESSED_MARKER = "#agent-work-done"
STATUS_FIELD_NAME = "status"
CLAIMED_BY_FIELD_NAME = "claimed_by"
CLAIMED_AT_FIELD_NAME = "claimed_at"
CLAIM_FIELD_NAMES = (STATUS_FIELD_NAME, CLAIMED_BY_FIELD_NAME, CLAIMED_AT_FIELD_NAME)
WORKING_STATUS_VALUE = "working"
DEFAULT_CLAIM_EXPIRY_MINUTES = 60
CLAIMABLE_STATES = ("unworked", "stale-claim")
CAPTURE_TIMESTAMP_IN_FILENAME = re.compile(
    r"(\d{4}-\d{2}-\d{2})[ _](\d{2})-(\d{2})-(\d{2})"
)


def default_capture_inbox_directory() -> Path:
    vault_directory = Path(os.environ.get("OBSIDIAN_HOME") or Path.home() / "vault")
    return vault_directory / "ReadItLater Inbox"


def resolve_capture_path(capture_inbox_directory: Path, capture_reference: str) -> Path:
    direct_path = Path(capture_reference).expanduser()
    if direct_path.is_file():
        return direct_path
    for candidate_path in (
        capture_inbox_directory / capture_reference,
        capture_inbox_directory / f"{capture_reference}.md",
    ):
        if candidate_path.is_file():
            return candidate_path
    raise FileNotFoundError(f"no capture matches {capture_reference!r}")


def read_capture_body(capture_path: Path) -> str:
    return capture_path.read_text(encoding="utf-8", errors="replace")


def inline_field_value(capture_body: str, field_name: str) -> str | None:
    field_prefix = f"{field_name}::"
    for capture_line in capture_body.splitlines():
        stripped_line = capture_line.strip()
        if stripped_line.startswith(field_prefix):
            return stripped_line[len(field_prefix) :].strip()
    return None


def capture_timestamp_from_filename(capture_filename: str) -> datetime | None:
    matched_timestamp = CAPTURE_TIMESTAMP_IN_FILENAME.search(capture_filename)
    if matched_timestamp is None:
        return None
    day, hour, minute, second = matched_timestamp.groups()
    try:
        return datetime.strptime(f"{day} {hour}:{minute}:{second}", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def capture_ordering_timestamp(capture_path: Path) -> datetime:
    timestamp_from_filename = capture_timestamp_from_filename(capture_path.name)
    if timestamp_from_filename is not None:
        return timestamp_from_filename
    return datetime.fromtimestamp(capture_path.stat().st_mtime).replace(microsecond=0)


def claim_timestamp(capture_body: str) -> datetime | None:
    raw_claim_timestamp = inline_field_value(capture_body, CLAIMED_AT_FIELD_NAME)
    if raw_claim_timestamp is None:
        return None
    try:
        return datetime.fromisoformat(raw_claim_timestamp)
    except ValueError:
        return None


def claim_has_expired(
    claimed_at: datetime | None, claim_expiry_minutes: int, now: datetime
) -> bool:
    if claimed_at is None:
        return True
    return now - claimed_at >= timedelta(minutes=claim_expiry_minutes)


def capture_state(capture_body: str, claim_expiry_minutes: int, now: datetime) -> str:
    if PROCESSED_MARKER in capture_body:
        return "done"
    if inline_field_value(capture_body, STATUS_FIELD_NAME) != WORKING_STATUS_VALUE:
        return "unworked"
    if claim_has_expired(claim_timestamp(capture_body), claim_expiry_minutes, now):
        return "stale-claim"
    return "working"


def describe_capture(
    capture_path: Path, claim_expiry_minutes: int, now: datetime
) -> dict[str, str | None]:
    capture_body = read_capture_body(capture_path)
    return {
        "name": capture_path.name,
        "path": str(capture_path),
        "captured": capture_ordering_timestamp(capture_path).isoformat(sep=" "),
        "captured_from": (
            "filename"
            if capture_timestamp_from_filename(capture_path.name)
            else "modification-time"
        ),
        "state": capture_state(capture_body, claim_expiry_minutes, now),
        "claimed_by": inline_field_value(capture_body, CLAIMED_BY_FIELD_NAME),
        "claimed_at": inline_field_value(capture_body, CLAIMED_AT_FIELD_NAME),
    }


def collect_pending_captures(
    capture_inbox_directory: Path,
    claim_expiry_minutes: int = DEFAULT_CLAIM_EXPIRY_MINUTES,
    now: datetime | None = None,
) -> list[dict[str, str | None]]:
    if not capture_inbox_directory.is_dir():
        return []
    resolved_now = now if now is not None else datetime.now()
    described_captures = [
        describe_capture(capture_path, claim_expiry_minutes, resolved_now)
        for capture_path in capture_inbox_directory.glob("*.md")
    ]
    return sorted(
        (capture for capture in described_captures if capture["state"] != "done"),
        key=lambda capture: (capture["captured"], capture["name"]),
        reverse=True,
    )


def claimable_captures(
    pending_captures: list[dict[str, str | None]],
) -> list[dict[str, str | None]]:
    return [
        capture for capture in pending_captures if capture["state"] in CLAIMABLE_STATES
    ]


def newest_pending_capture_fingerprint(
    pending_captures: list[dict[str, str | None]],
) -> str:
    if not pending_captures:
        return ""
    return f"{pending_captures[0]['captured']} {pending_captures[0]['name']}"
