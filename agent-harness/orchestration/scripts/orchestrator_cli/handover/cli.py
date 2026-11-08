from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..decisions.cards import ESCALATED_STATE, OPEN_STATE, withdrawn_card
from ..document_fields import InvalidPeerDocument
from ..peer_messenger import PeerMessageFailure, notify_peer, sender_name
from ..record_store import all_records, save_record, state_directory
from ..reports.status_reports import handed_over_report
from ..watch.herdr_events import HerdrUnavailable, move_pane_to_new_tab

HANDOVER_REASON = "handed over to the human, who drives this session directly now"
PEER_NOTICE = (
    "{orchestrator} handed you to Lucas: he drives this session directly from now on. "
    "Answer him in your pane, and stop filing decisions and reports to {orchestrator}."
)


def add_parser(subcommands) -> None:
    handover = subcommands.add_parser(
        "handover",
        help="give a sub-session to the human: close its cards, retire its report, "
        "tell it, and move its pane to a tab of its own",
    )
    handover.add_argument("pane", help="the sub-session's herdr pane id")
    handover.add_argument(
        "--for", dest="orchestrator", help="orchestrator name; defaults to yours"
    )
    handover.add_argument(
        "--dir", default=str(state_directory("orchestrator-decisions"))
    )
    handover.add_argument(
        "--reports-dir", default=str(state_directory("orchestrator-reports"))
    )


def belongs_to(record: dict, orchestrator: str, pane: str) -> bool:
    return (
        record["orchestrator"] == orchestrator and record.get("requester_pane") == pane
    )


def close_cards(directory: Path, orchestrator: str, pane: str) -> list[str]:
    closed = []
    for card in all_records(directory):
        if belongs_to(card, orchestrator, pane) and card["state"] in (
            OPEN_STATE,
            ESCALATED_STATE,
        ):
            closed_card = withdrawn_card(card, HANDOVER_REASON, orchestrator)
            save_record(directory, card["id"], closed_card)
            closed.append(f"closed {card['id']}")
    return closed


def retire_reports(directory: Path, orchestrator: str, pane: str) -> list[dict]:
    retired = []
    for report in all_records(directory):
        if belongs_to(report, orchestrator, pane):
            retired.append(handed_over_report(report))
            save_record(directory, report["name"], retired[-1])
    return retired


def hand_over(arguments: argparse.Namespace, orchestrator: str) -> list[str]:
    pane = arguments.pane
    lines = close_cards(Path(arguments.dir), orchestrator, pane)
    reports = retire_reports(Path(arguments.reports_dir), orchestrator, pane)
    lines += [f"retired report {report['name']}" for report in reports]
    label = reports[0]["requester"] if reports else pane
    lines.append(f"moved {pane} to tab {move_pane_to_new_tab(pane, label)}")
    print("\n".join(lines), flush=True)
    notify_peer(pane, orchestrator, PEER_NOTICE.format(orchestrator=orchestrator))
    return [f"told {pane} that Lucas drives it now"]


def command_handover(arguments: argparse.Namespace) -> int:
    try:
        orchestrator = arguments.orchestrator or sender_name(None)
        print("\n".join(hand_over(arguments, orchestrator)))
    except (PeerMessageFailure, HerdrUnavailable, InvalidPeerDocument) as failure:
        print(f"orchestrator handover: {failure}", file=sys.stderr)
        return 1
    return 0
