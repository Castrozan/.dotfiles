from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..decisions.cards import ESCALATED_STATE, OPEN_STATE, withdrawn_card
from ..document_fields import InvalidPeerDocument
from ..heartbeats.records import (
    HANDED_OVER_STATE,
    handed_over_heartbeat,
    taken_back_heartbeat,
)
from ..heartbeats.session_index import (
    closed_entry,
    entries_of,
    is_open,
    reopened_entry,
    save_entry,
)
from ..peer_messenger import (
    PeerAddress,
    PeerMessageFailure,
    notify_peer,
    sender_name,
)
from ..record_store import all_records, save_record, state_directory
from ..releases.released_sessions import (
    identity_of_pane,
    new_release,
    release_directory,
    releases_of,
    standing_releases,
    taken_back_release,
)
from ..watch.herdr_events import HerdrUnavailable, move_pane_to_new_tab

HANDOVER_REASON = "handed over to the human, who drives this session directly now"
RELEASE_NOTICE = (
    "{orchestrator} handed you to Lucas: he drives this session directly from now on. "
    "Answer him in your pane. This replaces your brief's Contract: send {orchestrator} "
    "no more heartbeats, decision cards or notifications; the orchestrator command "
    "refuses them from you now."
)
TAKE_BACK_NOTICE = (
    "Lucas handed you back to {orchestrator}, who orchestrates you again: publish "
    "heartbeats and file decision cards to {orchestrator} as your brief's Contract says. Cards closed "
    "at the handover stay closed, so file again whatever still needs deciding."
)


def add_parser(subcommands) -> None:
    handover = subcommands.add_parser(
        "handover",
        help="release a sub-session to the human: tell it, close its cards, retire "
        "its heartbeat, refuse what it files from then on, and move its pane to a tab "
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
        "--heartbeats-dir", default=str(state_directory("orchestrator-heartbeats"))
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


def session_heartbeats(
    directory: Path, orchestrator: str, panes: frozenset[str]
) -> list[dict]:
    return [
        heartbeat
        for heartbeat in all_records(directory)
        if belongs_to(heartbeat, orchestrator, panes)
    ]


def index_entries_on(orchestrator: str, panes: frozenset[str]) -> list[dict]:
    return [entry for entry in entries_of(orchestrator) if entry["pane"] in panes]


def close_index_entries(orchestrator: str, panes: frozenset[str]) -> list[str]:
    lines = []
    for entry in filter(is_open, index_entries_on(orchestrator, panes)):
        save_entry(closed_entry(entry, HANDOVER_REASON), Path(entry["heartbeat"]))
        lines.append(f"closed {entry['name']} in your index")
    return lines


def reopen_index_entries(orchestrator: str, panes: frozenset[str]) -> None:
    for entry in index_entries_on(orchestrator, panes):
        if entry["closed_because"] == HANDOVER_REASON:
            save_entry(reopened_entry(entry), Path(entry["heartbeat"]))
            print(f"reopened {entry['name']} in your index", flush=True)


def hand_over(arguments: argparse.Namespace, orchestrator: str) -> None:
    pane = arguments.pane
    identity = identity_of_pane(pane)
    heartbeats_directory = Path(arguments.heartbeats_dir)
    heartbeats = session_heartbeats(heartbeats_directory, orchestrator, identity.panes)
    label = heartbeats[0]["requester"] if heartbeats else pane
    release = new_release(pane, identity, label, orchestrator)
    save_record(release_directory(), release["name"], release)
    lines = close_cards(Path(arguments.dir), orchestrator, identity.panes)
    for heartbeat in heartbeats:
        if heartbeat["state"] != HANDED_OVER_STATE:
            save_record(
                heartbeats_directory,
                heartbeat["name"],
                handed_over_heartbeat(heartbeat),
            )
            lines.append(f"retired heartbeat {heartbeat['name']}")
    lines += close_index_entries(orchestrator, identity.panes)
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
    releases = releases_of(identity, standing_releases())
    if not releases:
        raise InvalidPeerDocument(f"{pane} is not released")
    for release in releases:
        save_record(release_directory(), release["name"], taken_back_release(release))
    heartbeats_directory = Path(arguments.heartbeats_dir)
    panes = identity.panes.union(*(release["panes"] for release in releases))
    for heartbeat in session_heartbeats(heartbeats_directory, orchestrator, panes):
        if heartbeat["state"] == HANDED_OVER_STATE:
            save_record(
                heartbeats_directory, heartbeat["name"], taken_back_heartbeat(heartbeat)
            )
            print(f"restored heartbeat {heartbeat['name']}", flush=True)
    reopen_index_entries(orchestrator, panes)
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
