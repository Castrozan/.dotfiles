from __future__ import annotations

import argparse
from datetime import datetime

from captures import (
    claimable_captures,
    collect_pending_captures,
    newest_pending_capture_fingerprint,
    resolve_capture_path,
)
from claims import (
    claim_capture,
    default_claim_owner,
    record_capture_verdict,
    release_capture,
)
from render import render_pending_captures_as_json, render_pending_captures_as_text

CLAIM_OUTCOME_EXIT_CODES = {
    "claimed": 0,
    "reclaimed": 0,
    "held": 1,
    "already-done": 1,
}


def command_list(arguments: argparse.Namespace) -> int:
    pending_captures = collect_pending_captures(
        arguments.inbox, arguments.expiry_minutes, datetime.now()
    )
    if arguments.claimable:
        pending_captures = claimable_captures(pending_captures)
    total_count = len(pending_captures)
    if arguments.limit > 0:
        pending_captures = pending_captures[: arguments.limit]
    render = (
        render_pending_captures_as_json
        if arguments.json
        else render_pending_captures_as_text
    )
    print(render(pending_captures, total_count))
    return 0


def command_claim(arguments: argparse.Namespace) -> int:
    capture_path = resolve_capture_path(arguments.inbox, arguments.capture)
    claim_outcome = claim_capture(
        capture_path,
        arguments.by or default_claim_owner(),
        arguments.expiry_minutes,
        datetime.now(),
        arguments.force,
    )
    print(f"{claim_outcome}: {capture_path.name}")
    return CLAIM_OUTCOME_EXIT_CODES[claim_outcome]


def command_release(arguments: argparse.Namespace) -> int:
    capture_path = resolve_capture_path(arguments.inbox, arguments.capture)
    release_outcome = release_capture(
        capture_path, arguments.expiry_minutes, datetime.now()
    )
    print(f"{release_outcome}: {capture_path.name}")
    return 0 if release_outcome == "released" else 1


def command_record(arguments: argparse.Namespace) -> int:
    capture_path = resolve_capture_path(arguments.inbox, arguments.capture)
    recording_outcome = record_capture_verdict(
        capture_path, arguments.verdict, arguments.outcome, arguments.entry
    )
    print(f"{recording_outcome}: {capture_path.name}")
    return 0 if recording_outcome == "recorded" else 1


def command_probe(arguments: argparse.Namespace) -> int:
    pending_captures = collect_pending_captures(
        arguments.inbox, arguments.expiry_minutes, datetime.now()
    )
    queue_head_fingerprint = newest_pending_capture_fingerprint(pending_captures)
    if queue_head_fingerprint:
        print(queue_head_fingerprint)
    return 0
