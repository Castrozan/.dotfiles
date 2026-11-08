from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from capture_queue.capture_content import (
    capture_kind,
    clipped_text,
    lucas_note,
    origin_url,
)
from capture_queue.captures import (
    claimable_captures,
    collect_pending_captures,
    read_capture_body,
)
from evidence.coverage import (
    Commit,
    closed_pull_requests_naming,
    commits_mentioning,
    read_commit_log,
)
from evidence.open_groups import captures_listed_in, open_groups
from forge_adapter import ForgeAdapter
from origins.routing import resolve_origin
from origins.transport import OriginTransport
from pull_requests import GROUP_BRANCH_PREFIX
from second_brain.index import entries_matching_origin, second_brain_index

ORIGIN_READ_WORKERS = 4
CLOSED_PULL_REQUEST_PREFIX = "ril-"


@dataclass(frozen=True)
class GatherSources:
    inbox_directory: Path
    vault_directory: Path
    repository_directory: Path
    forge: ForgeAdapter
    transport: OriginTransport


@dataclass(frozen=True)
class CoverageEvidence:
    closed_pull_requests: list[dict]
    commits: list[Commit]
    second_brain_entries: list[dict]


def capture_facts(capture: dict) -> dict:
    capture_body = read_capture_body(Path(str(capture["path"])))
    return {
        "name": capture["name"],
        "captured": capture["captured"],
        "kind": capture_kind(capture_body),
        "lucas_note": lucas_note(capture_body),
        "clipped_text": clipped_text(capture_body),
        "origin_url": origin_url(capture_body),
    }


def capture_evidence(facts: dict, origin: dict, coverage: CoverageEvidence) -> dict:
    origin_id = str(origin.get("origin_id") or "")
    return {
        "closed_pull_requests": closed_pull_requests_naming(
            coverage.closed_pull_requests, facts["name"], origin_id
        ),
        "commits": commits_mentioning(coverage.commits, origin_id),
        "second_brain_entries": [
            entry["title"]
            for entry in entries_matching_origin(
                coverage.second_brain_entries, facts["origin_url"], origin_id
            )
        ],
    }


def gathered_capture(
    capture: dict, sources: GatherSources, coverage: CoverageEvidence
) -> dict:
    facts = capture_facts(capture)
    origin = resolve_origin(facts["origin_url"], sources.transport)
    return {
        **facts,
        "origin": origin,
        "evidence": capture_evidence(facts, origin, coverage),
    }


def captures_to_triage(
    sources: GatherSources, listed_captures: set[str], now: datetime
) -> list[dict]:
    local_now = now.astimezone().replace(tzinfo=None)
    pending = claimable_captures(
        collect_pending_captures(sources.inbox_directory, now=local_now)
    )
    return [capture for capture in pending if capture["name"] not in listed_captures]


def gather_document(sources: GatherSources, now: datetime) -> dict:
    groups = open_groups(
        sources.repository_directory,
        sources.forge.open_pull_requests(GROUP_BRANCH_PREFIX),
    )
    index = second_brain_index(sources.vault_directory)
    coverage = CoverageEvidence(
        closed_pull_requests=sources.forge.closed_pull_requests(
            CLOSED_PULL_REQUEST_PREFIX
        ),
        commits=read_commit_log(sources.repository_directory),
        second_brain_entries=index["entries"],
    )
    captures = captures_to_triage(sources, captures_listed_in(groups), now)
    with ThreadPoolExecutor(max_workers=ORIGIN_READ_WORKERS) as executor:
        gathered = list(
            executor.map(
                lambda capture: gathered_capture(capture, sources, coverage), captures
            )
        )
    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "captures": gathered,
        "open_groups": groups,
        "second_brain": index,
    }
