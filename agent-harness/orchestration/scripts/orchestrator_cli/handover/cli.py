from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..decisions.cards import ESCALATED_STATE, OPEN_STATE, withdrawn_card
from ..document_fields import InvalidPeerDocument
from ..peer_messenger import (
    PeerAddress,
    PeerMessageFailure,
    notify_peer,
    sender_name,
)
from ..record_store import all_records, delete_record, save_record, state_directory
from ..releases.released_sessions import (
    identity_of_pane,
    new_release,
    release_directory,
    releases_of,
)
from ..reports.status_reports import (
    HANDED_OVER_STATE,
    handed_over_report,
    taken_back_report,
)
from ..watch.herdr_events import HerdrUnavailable, move_pane_to_new_tab

HANDOVER_REASON = "handed over to the human, who drives this session directly now"
RELEASE_NOTICE = (
    "{orchestrator} handed you to Lucas: he drives this session directly from now on. "
    "Answer him in your pane. This replaces your brief's Contract: send {orchestrator} "
    "no more reports, decision cards or notifications; the orchestrator command "
    "refuses them from you now."
)
TAKE_BACK_NOTICE = (
    "Lucas handed you back to {orchestrator}, who orchestrates you again: file reports "
    "and decision cards to {orchestrator} as your brief's Contract says. Cards closed "
    "at the handover stay closed, so file again whatever still needs deciding."
)


def add_parser(subcommands) -> None:
    handover = subcommands.add_parser(
        "handover",
        help="release a sub-session to the human: tell it, close its cards, retire "
        "its report, refuse what it files from then on, and move its pane to a tab "
        "of its own",
    )
    handover.add_argument("pane", help="the sub-session's herdr pane id")
    placement = handover.add_mutually_exclusive_group()
    placement.add_argument(
        "--no-move",
        action="store_true",
        help="leave the pane where it is, when the human already placed it",
    )
    placement.add_argument(
        "--take-back",
        action="store_true",
        help="the human handed the session back: lift its release and tell it",
    )
    handover.add_argument(
        "--for", dest="orchestrator", help="orchestrator name; defaults to yours"
    )
    handover.add_argument(
        "--dir", default=str(state_directory("orchestrator-decisions"))
    )
    handover.add_argument(
        "--reports-dir", default=str(state_directory("orchestrator-reports"))
    )


def belongs_to(record: dict, orchestrator: str, panes: frozenset[str]) -> bool:
    return (
        record["orchestrator"] == orchestrator and record.get("requester_pane") in panes
    )


def close_cards(directory: Path, orchestrator: str, panes: frozenset[str]) -> list[str]:
    closed = []
    for card in all_records(directory):
        if belongs_to(card, orchestrator, panes) and card["state"] in (
            OPEN_STATE,
            ESCALATED_STATE,
        ):
            closed_card = withdrawn_card(card, HANDOVER_REASON, orchestrator)
            save_record(directory, card["id"], closed_card)
            closed.append(f"closed {card['id']}")
    return closed


def session_reports(
    directory: Path, orchestrator: str, panes: frozenset[str]
) -> list[dict]:
    return [
        report
        for report in all_records(directory)
        if belongs_to(report, orchestrator, panes)
    ]


def hand_over(arguments: argparse.Namespace, orchestrator: str) -> None:
    pane = arguments.pane
    identity = identity_of_pane(pane)
    reports_directory = Path(arguments.reports_dir)
    reports = session_reports(reports_directory, orchestrator, identity.panes)
    label = reports[0]["requester"] if reports else pane
    release = new_release(pane, identity, label, orchestrator)
    save_record(release_directory(), release["name"], release)
    lines = close_cards(Path(arguments.dir), orchestrator, identity.panes)
    for report in reports:
        save_record(reports_directory, report["name"], handed_over_report(report))
        lines.append(f"retired report {report['name']}")
    lines.append(f"released {label}: what it files from now on is refused")
    print("\n".join(lines), flush=True)
    notify_peer(
        PeerAddress(pane),
        orchestrator,
        RELEASE_NOTICE.format(orchestrator=orchestrator),
    )
    print(f"told {pane} that Lucas drives it now", flush=True)
    if not arguments.no_move:
        print(f"moved {pane} to tab {move_pane_to_new_tab(pane, label)}")


def take_back(arguments: argparse.Namespace, orchestrator: str) -> None:
    pane = arguments.pane
    identity = identity_of_pane(pane)
    releases = releases_of(identity, all_records(release_directory()))
    if not releases:
        raise InvalidPeerDocument(f"{pane} is not released")
    for release in releases:
        delete_record(release_directory(), release["name"])
    reports_directory = Path(arguments.reports_dir)
    for report in session_reports(reports_directory, orchestrator, identity.panes):
        if report["state"] == HANDED_OVER_STATE:
            save_record(reports_directory, report["name"], taken_back_report(report))
            print(f"restored report {report['name']}", flush=True)
    print(f"took {pane} back: what it files reaches you again", flush=True)
    notify_peer(
        PeerAddress(pane),
        orchestrator,
        TAKE_BACK_NOTICE.format(orchestrator=orchestrator),
    )
    print(f"told {pane} that {orchestrator} orchestrates it again")


def command_handover(arguments: argparse.Namespace) -> int:
    try:
        orchestrator = arguments.orchestrator or sender_name(None)
        if arguments.take_back:
            take_back(arguments, orchestrator)
        else:
            hand_over(arguments, orchestrator)
    except (PeerMessageFailure, HerdrUnavailable, InvalidPeerDocument) as failure:
        print(f"orchestrator handover: {failure}", file=sys.stderr)
        return 1
    return 0
