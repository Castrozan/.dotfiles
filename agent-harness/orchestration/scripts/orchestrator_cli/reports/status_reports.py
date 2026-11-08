from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass

from ..document_fields import (
    InvalidPeerDocument,
    current_timestamp,
    nonempty_text,
    optional_text_items,
    require_object,
)

REPORT_STATES = ("working", "blocked", "done")
ATTENTION_STATES = frozenset({"blocked", "done"})
REQUIRED_TEXT_FIELDS = ("goal", "done_check", "progress", "next_step")


def report_name(requester: str) -> str:
    ascii_name = (
        unicodedata.normalize("NFKD", requester).encode("ascii", "ignore").decode()
    )
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", ascii_name).strip("-.")
    if not name:
        raise InvalidPeerDocument(f"{requester!r} cannot name a report")
    return name


def validated_claim(claim) -> dict:
    claim = require_object(claim, "each verified claim")
    return {
        "claim": nonempty_text(claim, "claim"),
        "evidence": nonempty_text(claim, "evidence"),
    }


def validated_report_fields(document) -> dict:
    document = require_object(document, "the report")
    report = {field: nonempty_text(document, field) for field in REQUIRED_TEXT_FIELDS}
    if document.get("state") not in REPORT_STATES:
        raise InvalidPeerDocument(f"state must be one of {', '.join(REPORT_STATES)}")
    report["state"] = document["state"]
    verified = document.get("verified", [])
    if not isinstance(verified, list):
        raise InvalidPeerDocument("verified must be a list of claim and evidence pairs")
    report["verified"] = [validated_claim(claim) for claim in verified]
    report["unverified"] = optional_text_items(document, "unverified")
    report["open_decisions"] = optional_text_items(document, "open_decisions")
    return report


@dataclass(frozen=True)
class ReportAuthor:
    name: str
    requester: str
    requester_pane: str | None
    orchestrator: str


def new_status_report(
    document, author: ReportAuthor, previous_state: str | None
) -> dict:
    return {
        **asdict(author),
        "updated_at": current_timestamp(),
        "previous_state": previous_state,
        **validated_report_fields(document),
    }


def needs_orchestrator_attention(report: dict) -> bool:
    return (
        report["state"] in ATTENTION_STATES
        and report["state"] != report["previous_state"]
    )


def rendered_report(report: dict) -> str:
    lines = [
        f"## {report['requester']} · {report['state']} · {report['updated_at']}",
        "",
        f"**Goal**: {report['goal']}",
        f"**Done when**: {report['done_check']}",
        f"**Progress**: {report['progress']}",
        f"**Next**: {report['next_step']}",
    ]
    if report["verified"]:
        lines += ["", "**Verified**"]
        lines += [
            f"- {item['claim']} ({item['evidence']})" for item in report["verified"]
        ]
    if report["unverified"]:
        lines += [
            "",
            "**Not verified**",
            *(f"- {item}" for item in report["unverified"]),
        ]
    if report["open_decisions"]:
        lines += ["", f"**Open decisions**: {', '.join(report['open_decisions'])}"]
    return "\n".join(lines)


def summary_row(report: dict) -> str:
    return "\t".join(
        [
            report["name"],
            report["requester"],
            report["state"],
            report["updated_at"],
            report["goal"],
            report["next_step"],
        ]
    )


def notification_text(report: dict) -> str:
    return (
        f"{report['requester']} is {report['state']}: {report['next_step']} "
        f"Read it: orchestrator report show {report['name']}"
    )
