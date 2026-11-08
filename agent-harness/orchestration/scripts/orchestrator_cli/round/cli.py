from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from ..peer_messenger import PeerMessageFailure, sender_name
from ..record_store import all_records, state_directory
from .rendering import rendered_round

WAITING_STATE = "escalated"


def add_parser(subcommands) -> None:
    round_command = subcommands.add_parser(
        "round",
        help="the turn-end view for the human: each decision waiting for them with "
        "every option, then one row per session; relay it in a fenced block",
    )
    round_command.add_argument(
        "--dir", default=str(state_directory("orchestrator-decisions"))
    )
    round_command.add_argument(
        "--reports-dir", default=str(state_directory("orchestrator-reports"))
    )
    round_command.add_argument(
        "--for", dest="orchestrator", help="orchestrator name; defaults to yours"
    )


def addressed_to(records: list[dict], orchestrator: str) -> list[dict]:
    return [record for record in records if record["orchestrator"] == orchestrator]


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
    reports = addressed_to(all_records(Path(arguments.reports_dir)), orchestrator)
    print(
        rendered_round(
            sorted(cards, key=lambda card: card["created_at"]),
            sorted(reports, key=lambda report: report["requester"]),
            datetime.now(timezone.utc),
        )
    )
    return 0
