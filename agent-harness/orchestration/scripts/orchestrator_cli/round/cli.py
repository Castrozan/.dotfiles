from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..ledger.entries import open_asks
from ..peer_messenger import PeerMessageFailure, sender_name
from ..record_store import all_records, state_directory
from ..reports.status_reports import HANDED_OVER_STATE
from .rendering import rendered_round

WAITING_STATE = "escalated"
FINISHED_STATE = "done"
FINISHED_VISIBLE_FOR = timedelta(minutes=30)


def add_parser(subcommands) -> None:
    round_command = subcommands.add_parser(
        "round",
        help="the turn-end view for the human: one row per session, their requests "
        "not yet verified done, then each decision waiting for them with every "
        "option; relay it verbatim as Markdown",
    )
    round_command.add_argument(
        "--dir", default=str(state_directory("orchestrator-decisions"))
    )
    round_command.add_argument(
        "--reports-dir", default=str(state_directory("orchestrator-reports"))
    )
    round_command.add_argument(
        "--ledger-dir", default=str(state_directory("orchestrator-ledger"))
    )
    round_command.add_argument(
        "--for", dest="orchestrator", help="orchestrator name; defaults to yours"
    )


def addressed_to(records: list[dict], orchestrator: str) -> list[dict]:
    return [record for record in records if record["orchestrator"] == orchestrator]


def still_relevant(report: dict, now: datetime) -> bool:
    if report["state"] == HANDED_OVER_STATE:
        return False
    finished_long_ago = (
        now - datetime.fromisoformat(report["updated_at"]) > FINISHED_VISIBLE_FOR
    )
    return not (report["state"] == FINISHED_STATE and finished_long_ago)


def visible_reports(reports: list[dict], now: datetime) -> list[dict]:
    relevant = [report for report in reports if still_relevant(report, now)]
    return sorted(relevant, key=lambda report: report["name"])


def command_round(arguments: argparse.Namespace) -> int:
    try:
        orchestrator = arguments.orchestrator or sender_name(None)
    except PeerMessageFailure as failure:
        print(f"orchestrator round: {failure}", file=sys.stderr)
        return 1
    cards = [
        card
        for card in addressed_to(all_records(Path(arguments.dir)), orchestrator)
        if card["state"] == WAITING_STATE
    ]
    now = datetime.now(timezone.utc)
    reports = addressed_to(all_records(Path(arguments.reports_dir)), orchestrator)
    asks = open_asks(all_records(Path(arguments.ledger_dir)), orchestrator)
    print(
        rendered_round(
            sorted(cards, key=lambda card: card["created_at"]),
            visible_reports(reports, now),
            asks,
            now,
            orchestrator,
        )
    )
    return 0
