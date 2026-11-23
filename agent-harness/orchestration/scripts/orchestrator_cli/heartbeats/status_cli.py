from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from ..document_fields import InvalidPeerDocument
from ..peer_messenger import PeerMessageFailure, sender_name
from ..watch.herdr_events import UNKNOWN_STATUS, pane_agent_status
from .session_index import (
    closed_entry,
    entries_of,
    is_open,
    named_entry,
    save_entry,
)
from .status import SessionStatus, published_heartbeat_of, rendered_status

DEFAULT_STALE_MINUTES = 15


def add_status_parser(subcommands) -> None:
    status = subcommands.add_parser(
        "status",
        help="every session in your index from its heartbeat file: open ones with "
        "what they do, next step and flags for a stale heartbeat or a pane that "
        "contradicts it, then closed ones, then where each heartbeat file lives",
    )
    status.add_argument("--for", dest="orchestrator", help="defaults to yours")
    status.add_argument(
        "--stale-minutes",
        type=int,
        default=DEFAULT_STALE_MINUTES,
        help="flag a working or waiting heartbeat older than this",
    )
    status.set_defaults(handler=command_status)


def add_close_parser(subcommands) -> None:
    close = subcommands.add_parser(
        "close",
        help="move a session to the closed part of your index once you verified "
        "its goal done or stopped it",
    )
    close.add_argument("session", help="index name, pane id or peer name")
    close.add_argument("--because", required=True, help="what proves it done, or why")
    close.add_argument("--for", dest="orchestrator", help="defaults to yours")
    close.set_defaults(handler=command_close)


def pane_status(entry: dict) -> str:
    if entry["host"]:
        return f"on {entry['host']}"
    return pane_agent_status(entry["pane"]) if entry["pane"] else UNKNOWN_STATUS


def session_status(entry: dict) -> SessionStatus:
    return SessionStatus(entry, published_heartbeat_of(entry), pane_status(entry))


def command_status(arguments: argparse.Namespace, orchestrator: str) -> int:
    entries = sorted(entries_of(orchestrator), key=lambda entry: entry["opened_at"])
    statuses = [session_status(entry) for entry in entries if is_open(entry)]
    closed = [entry for entry in entries if not is_open(entry)]
    now = datetime.now(timezone.utc)
    print(rendered_status(statuses, closed, now, arguments.stale_minutes))
    return 0


def command_close(arguments: argparse.Namespace, orchestrator: str) -> int:
    open_entries = [entry for entry in entries_of(orchestrator) if is_open(entry)]
    entry = closed_entry(
        named_entry(open_entries, arguments.session), arguments.because
    )
    save_entry(entry, Path(entry["heartbeat"]))
    print(f"closed {entry['name']}")
    return 0


def command_index(arguments: argparse.Namespace) -> int:
    try:
        orchestrator = arguments.orchestrator or sender_name(None)
        return arguments.handler(arguments, orchestrator)
    except (InvalidPeerDocument, PeerMessageFailure) as failure:
        print(f"orchestrator {arguments.command}: {failure}", file=sys.stderr)
        return 1
