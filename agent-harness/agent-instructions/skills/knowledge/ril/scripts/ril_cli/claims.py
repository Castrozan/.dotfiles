from __future__ import annotations

import socket
from datetime import datetime
from pathlib import Path

from captures import (
    CLAIM_FIELD_NAMES,
    CLAIMED_AT_FIELD_NAME,
    CLAIMED_BY_FIELD_NAME,
    PROCESSED_MARKER,
    STATUS_FIELD_NAME,
    WORKING_STATUS_VALUE,
    capture_state,
    read_capture_body,
)

VERDICT_CHOICES = ("adopt", "trial", "learn", "reference", "drop")
RELEASABLE_STATES = ("working", "stale-claim")


def default_claim_owner() -> str:
    return socket.gethostname()


def build_claim_block(claim_owner: str, claimed_at: datetime) -> str:
    claim_lines = [
        f"{STATUS_FIELD_NAME}:: {WORKING_STATUS_VALUE}",
        f"{CLAIMED_BY_FIELD_NAME}:: {claim_owner}",
        f"{CLAIMED_AT_FIELD_NAME}:: {claimed_at.isoformat(timespec='seconds')}",
    ]
    return "\n".join(claim_lines) + "\n"


def build_verdict_block(
    verdict: str, outcome: str, second_brain_entry: str | None
) -> str:
    verdict_lines = [PROCESSED_MARKER, f"verdict:: {verdict}", f"outcome:: {outcome}"]
    if second_brain_entry:
        normalized_entry = second_brain_entry.strip().strip("[]")
        verdict_lines.append(f"entry:: [[{normalized_entry}]]")
    return "\n".join(verdict_lines) + "\n"


def strip_claim_fields(capture_body: str) -> str:
    claim_field_prefixes = tuple(f"{field_name}::" for field_name in CLAIM_FIELD_NAMES)
    kept_lines = [
        capture_line
        for capture_line in capture_body.splitlines()
        if not capture_line.strip().startswith(claim_field_prefixes)
    ]
    return "\n".join(kept_lines).rstrip()


def write_capture_with_block(capture_path: Path, capture_body: str, block: str) -> None:
    capture_path.write_text(
        f"{strip_claim_fields(capture_body)}\n\n{block}", encoding="utf-8"
    )


def claim_capture(
    capture_path: Path,
    claim_owner: str,
    claim_expiry_minutes: int,
    now: datetime,
    force: bool = False,
) -> str:
    capture_body = read_capture_body(capture_path)
    current_state = capture_state(capture_body, claim_expiry_minutes, now)
    if current_state == "done":
        return "already-done"
    if current_state == "working" and not force:
        return "held"
    write_capture_with_block(
        capture_path, capture_body, build_claim_block(claim_owner, now)
    )
    return "claimed" if current_state == "unworked" else "reclaimed"


def release_capture(
    capture_path: Path, claim_expiry_minutes: int, now: datetime
) -> str:
    capture_body = read_capture_body(capture_path)
    if capture_state(capture_body, claim_expiry_minutes, now) not in RELEASABLE_STATES:
        return "not-claimed"
    capture_path.write_text(f"{strip_claim_fields(capture_body)}\n", encoding="utf-8")
    return "released"


def record_capture_verdict(
    capture_path: Path, verdict: str, outcome: str, second_brain_entry: str | None
) -> str:
    capture_body = read_capture_body(capture_path)
    if PROCESSED_MARKER in capture_body:
        return "already-recorded"
    write_capture_with_block(
        capture_path,
        capture_body,
        build_verdict_block(verdict, outcome, second_brain_entry),
    )
    return "recorded"
