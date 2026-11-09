from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..document_fields import InvalidPeerDocument, require_bounded_line
from ..peer_messenger import (
    PeerAddress,
    PeerMessageFailure,
    copy_file_to_host,
    notify_peer,
    requester_address,
    sender_name,
)
from ..record_store import all_records, state_directory
from .brief_template import brief_problems

FACT_CHARACTERS = 200
FACT_ADVICE = "relay one fact and let the session work out what follows from it"
STATUS_CHECK_TEXT = (
    "Status check: you have been quiet a while. File your current report or the card "
    "you owe, and check that your background commands are still alive; a broken one "
    "may never notify you."
)
SESSION_LOOKUP_KEYS = ("name", "requester_pane", "requester")


def add_dispatch_parser(subcommands) -> None:
    dispatch = subcommands.add_parser(
        "dispatch",
        help="check a brief against the template, then hand it to a sub-session",
    )
    dispatch.add_argument("target", help="the session's pane id, peer or Servant name")
    dispatch.add_argument("--brief", required=True, help="the brief file")
    dispatch.add_argument(
        "--host",
        help="ssh alias of the session's machine; the brief is copied to the same path",
    )
    dispatch.set_defaults(handler=command_dispatch)


def add_relay_parser(subcommands) -> None:
    relay = subcommands.add_parser(
        "relay",
        help="send a sub-session Lucas's words, a new fact or a status check; "
        "the session plans what to do about it",
    )
    relay.add_argument("session", help="report name, pane id or requester name")
    content = relay.add_mutually_exclusive_group(required=True)
    content.add_argument("--words", help="Lucas's words, verbatim")
    content.add_argument("--fact", help="one new fact, one line")
    content.add_argument(
        "--status-check",
        action="store_true",
        help="ask for the owed report or card and whether background jobs live",
    )
    relay.add_argument(
        "--reports-dir", default=str(state_directory("orchestrator-reports"))
    )
    relay.set_defaults(handler=command_relay)


def dispatch_text(brief: Path) -> str:
    return (
        f"New task: read {brief} and carry it out. You plan the steps; its Contract "
        "says what to file and when."
    )


def command_dispatch(arguments: argparse.Namespace) -> int:
    brief = Path(arguments.brief).expanduser().resolve()
    problems = brief_problems(brief.read_text(encoding="utf-8"), arguments.host)
    for problem in problems:
        print(f"orchestrator dispatch: {brief}: {problem}", file=sys.stderr)
    if problems:
        return 1
    if arguments.host:
        copy_file_to_host(brief, arguments.host)
    address = PeerAddress(arguments.target, arguments.host)
    notify_peer(address, sender_name(None), dispatch_text(brief))
    print(f"sent {brief} to {address}")
    return 0


def session_address(reports_directory: Path, session: str) -> PeerAddress:
    reports = all_records(reports_directory)
    for key in SESSION_LOOKUP_KEYS:
        matches = [report for report in reports if report.get(key) == session]
        addresses = {requester_address(report) for report in matches}
        if len(addresses) > 1:
            names = ", ".join(sorted(report["name"] for report in matches))
            raise InvalidPeerDocument(
                f"{session} matches several sessions ({names}); name one of them"
            )
        if addresses:
            return addresses.pop()
    return PeerAddress(session)


def words_relay_text(words: str) -> str:
    flat = " ".join(words.split())
    return f'Lucas\'s words: "{flat}". You decide what they change in your plan.'


def relay_text(arguments: argparse.Namespace) -> str:
    if arguments.status_check:
        return STATUS_CHECK_TEXT
    if arguments.words is not None:
        return words_relay_text(arguments.words)
    fact = arguments.fact.strip()
    require_bounded_line("the fact", fact, FACT_CHARACTERS, FACT_ADVICE)
    return f"New fact: {fact.rstrip('.')}. You decide what it changes in your plan."


def command_relay(arguments: argparse.Namespace) -> int:
    text = relay_text(arguments)
    address = session_address(Path(arguments.reports_dir), arguments.session)
    notify_peer(address, sender_name(None), text)
    print(f"relayed to {address}")
    return 0


def command_session_message(arguments: argparse.Namespace) -> int:
    try:
        return arguments.handler(arguments)
    except (InvalidPeerDocument, PeerMessageFailure, OSError) as failure:
        print(f"orchestrator {arguments.command}: {failure}", file=sys.stderr)
        return 1
