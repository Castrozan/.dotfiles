from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..document_fields import InvalidPeerDocument, require_bounded_line
from ..heartbeats.records import heartbeat_name
from ..heartbeats.session_index import (
    SessionPlacement,
    entries_of,
    filer_entry,
    new_entry,
    save_entry,
)
from ..peer_messenger import (
    PeerAddress,
    PeerMessageFailure,
    copy_file_to_host,
    notify_peer,
    peer_record,
    requester_address,
    sender_name,
)
from ..record_store import all_records, record_path, state_directory
from ..releases.released_sessions import SessionReleased, require_unreleased_target
from .brief_template import brief_goal, brief_problems

FACT_CHARACTERS = 200
FACT_ADVICE = "relay one fact and let the session work out what follows from it"
STATUS_CHECK_TEXT = (
    "Status check: you have been quiet a while. Publish your current heartbeat or the card "
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
    dispatch.add_argument(
        "--heartbeats-dir", default=str(state_directory("orchestrator-heartbeats"))
    )
    dispatch.set_defaults(handler=command_dispatch)


def add_relay_parser(subcommands) -> None:
    relay = subcommands.add_parser(
        "relay",
        help="send a sub-session Lucas's words, a new fact or a status check; "
        "the session plans what to do about it",
    )
    relay.add_argument("session", help="heartbeat name, pane id or requester name")
    content = relay.add_mutually_exclusive_group(required=True)
    content.add_argument("--words", help="Lucas's words, verbatim")
    content.add_argument("--fact", help="one new fact, one line")
    content.add_argument(
        "--status-check",
        action="store_true",
        help="ask for the owed heartbeat or card and whether background jobs live",
    )
    relay.add_argument(
        "--heartbeats-dir", default=str(state_directory("orchestrator-heartbeats"))
    )
    relay.set_defaults(handler=command_relay)


def dispatch_text(brief: Path) -> str:
    return (
        f"New task: read {brief} and carry it out. You plan the steps; its Contract "
        "says what to file and when."
    )


def live_peer(target: str, host: str | None) -> dict:
    agent = peer_record(target, host)
    if agent is None:
        where = f" on {host}" if host else ""
        raise InvalidPeerDocument(f"a2a list shows no live session {target}{where}")
    return agent


def dispatched_name(agent: dict, arguments, placement: SessionPlacement) -> str:
    label = agent.get("servant") or agent.get("name") or arguments.target
    return heartbeat_name(
        " ".join(filter(None, [label, arguments.host, placement.pane]))
    )


def indexed_dispatch(arguments, brief: Path, goal: str, orchestrator: str) -> str:
    agent = live_peer(arguments.target, arguments.host)
    names = filter(None, (agent.get(key) for key in ("name", "servant", "paneId")))
    placement = SessionPlacement(arguments.host, agent.get("paneId"), frozenset(names))
    known = filer_entry(entries_of(orchestrator), placement)
    name = known["name"] if known else dispatched_name(agent, arguments, placement)
    entry = new_entry(name, orchestrator, placement, goal, str(brief))
    return save_entry(entry, record_path(Path(arguments.heartbeats_dir), name))["name"]


def command_dispatch(arguments: argparse.Namespace) -> int:
    brief = Path(arguments.brief).expanduser().resolve()
    text = brief.read_text(encoding="utf-8")
    problems = brief_problems(text, arguments.host)
    for problem in problems:
        print(f"orchestrator dispatch: {brief}: {problem}", file=sys.stderr)
    if problems:
        return 1
    if arguments.host:
        copy_file_to_host(brief, arguments.host)
    else:
        require_unreleased_target(arguments.target)
    orchestrator = sender_name(None)
    name = indexed_dispatch(arguments, brief, brief_goal(text), orchestrator)
    address = PeerAddress(arguments.target, arguments.host)
    notify_peer(address, orchestrator, dispatch_text(brief))
    print(f"sent {brief} to {address}; indexed as {name}")
    return 0


def session_address(heartbeats_directory: Path, session: str) -> PeerAddress:
    heartbeats = all_records(heartbeats_directory)
    for key in SESSION_LOOKUP_KEYS:
        matches = [
            heartbeat for heartbeat in heartbeats if heartbeat.get(key) == session
        ]
        addresses = {requester_address(heartbeat) for heartbeat in matches}
        if len(addresses) > 1:
            names = ", ".join(sorted(heartbeat["name"] for heartbeat in matches))
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
    address = session_address(Path(arguments.heartbeats_dir), arguments.session)
    if address.host is None:
        require_unreleased_target(address.target)
    notify_peer(address, sender_name(None), text)
    print(f"relayed to {address}")
    return 0


def command_session_message(arguments: argparse.Namespace) -> int:
    try:
        return arguments.handler(arguments)
    except (
        InvalidPeerDocument,
        PeerMessageFailure,
        SessionReleased,
        OSError,
    ) as failure:
        print(f"orchestrator {arguments.command}: {failure}", file=sys.stderr)
        return 1
