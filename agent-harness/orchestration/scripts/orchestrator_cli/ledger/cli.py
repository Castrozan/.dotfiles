from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..document_fields import InvalidPeerDocument
from ..peer_messenger import PeerMessageFailure, notify_peer, sender_name
from ..record_store import all_records, load_record, save_record, state_directory
from ..session_messages.cli import session_address, words_relay_text
from .entries import (
    ASK_KIND,
    DONE_STATE,
    FACT_KIND,
    closed_entry,
    entries_of,
    new_entry,
)

ENTRY_HELP = {
    ASK_KIND: "something Lucas wants done; it stays in the round until closed",
    FACT_KIND: "something Lucas tells you is true, such as an approval given or a "
    "request sent; it stays on record",
}


def add_parser(subcommands) -> None:
    ledger = subcommands.add_parser(
        "ledger",
        help="keep what Lucas gives you: every ask stays open in the round until you "
        "close it with evidence, every fact stays on record, and --to hands his words "
        "to the session they concern",
    )
    ledger.add_argument("--dir", default=str(state_directory("orchestrator-ledger")))
    commands = ledger.add_subparsers(dest="ledger_command", required=True)
    for kind, help_text in ENTRY_HELP.items():
        entry = commands.add_parser(kind, help=help_text)
        entry.add_argument("--words", required=True, help="Lucas's words, verbatim")
        entry.add_argument(
            "--to", help="the session it concerns; it receives his words now"
        )
        entry.add_argument(
            "--reports-dir", default=str(state_directory("orchestrator-reports"))
        )
        entry.set_defaults(handler=command_record, kind=kind)
    close = commands.add_parser(
        "close", help="close an ask once live state, not a report, proves it done"
    )
    close.add_argument("identifier")
    close.add_argument("--evidence", required=True, help="what proves it done")
    close.set_defaults(handler=command_close)
    listing = commands.add_parser(
        "list", help="open asks and every fact on record, oldest first"
    )
    listing.add_argument("--all", action="store_true", help="include closed asks")
    listing.set_defaults(handler=command_list)


def command_record(arguments: argparse.Namespace) -> int:
    orchestrator = sender_name(None)
    entry = new_entry(arguments.kind, arguments.words, arguments.to, orchestrator)
    save_record(Path(arguments.dir), entry["id"], entry)
    print(f"recorded {entry['id']}")
    if arguments.to:
        address = session_address(Path(arguments.reports_dir), arguments.to)
        notify_peer(address, orchestrator, words_relay_text(entry["words"]))
        print(f"relayed to {address}")
    return 0


def command_close(arguments: argparse.Namespace) -> int:
    directory = Path(arguments.dir)
    entry = closed_entry(
        load_record(directory, arguments.identifier), arguments.evidence
    )
    save_record(directory, entry["id"], entry)
    print(f"closed {entry['id']}")
    return 0


def listed_line(entry: dict) -> str:
    words = " ".join(entry["words"].split())
    closing = f" · {entry['evidence']}" if entry["state"] == DONE_STATE else ""
    return (
        f"{entry['id']} {entry['kind']} {entry['state']} · {entry['owner']} · "
        f"{entry['recorded_at']} · {words}{closing}"
    )


def command_list(arguments: argparse.Namespace) -> int:
    entries = entries_of(all_records(Path(arguments.dir)), sender_name(None))
    shown = [
        entry for entry in entries if arguments.all or entry["state"] != DONE_STATE
    ]
    for entry in shown:
        print(listed_line(entry))
    if not shown:
        print("Nothing Lucas gave you is on record.")
    return 0


def command_ledger(arguments: argparse.Namespace) -> int:
    try:
        return arguments.handler(arguments)
    except (InvalidPeerDocument, PeerMessageFailure, OSError) as failure:
        print(f"orchestrator ledger: {failure}", file=sys.stderr)
        return 1
