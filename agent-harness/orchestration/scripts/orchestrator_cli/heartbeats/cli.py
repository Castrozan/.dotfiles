from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import replace
from pathlib import Path

from ..document_fields import InvalidPeerDocument
from ..peer_messenger import (
    PeerAddress,
    PeerMessageFailure,
    notify_after_save,
    sender_name,
)
from ..record_store import load_record, save_record, state_directory
from ..releases.released_sessions import SessionReleased, require_unreleased_filer
from .records import (
    HeartbeatAuthor,
    heartbeat_name,
    needs_orchestrator_attention,
    notification_text,
    published_heartbeat,
    rendered_record,
)
from .session_index import (
    SessionPlacement,
    entries_of,
    filer_entry,
    new_entry,
    save_entry,
)
from .template import HEARTBEAT_TEMPLATE, parsed_heartbeat

HEARTBEAT_CONTRACT = (
    "Keep this file as HEARTBEAT.md at your worktree root; re-read it before each step\n"
    "and after compaction. Publish it with\n"
    "`orchestrator heartbeat file --to <orchestrator> < HEARTBEAT.md` whenever a line\n"
    "changes and at least every 10 minutes while working. State waiting means idle\n"
    "until your own background job ends; blocked means a filed decision card holds you.\n\n"
)


def add_parser(subcommands) -> None:
    heartbeat = subcommands.add_parser(
        "heartbeat",
        help="a session's HEARTBEAT.md: what it does now, next and has done, "
        "published to its orchestrator",
    )
    heartbeat.add_argument(
        "--dir", default=str(state_directory("orchestrator-heartbeats"))
    )
    commands = heartbeat.add_subparsers(dest="heartbeat_command", required=True)

    file_command = commands.add_parser(
        "file",
        help="publish HEARTBEAT.md from stdin; notifies only on turning blocked or done",
        epilog=HEARTBEAT_CONTRACT + HEARTBEAT_TEMPLATE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    file_command.add_argument("--to", required=True, help="orchestrator peer target")
    file_command.add_argument("--sender", help="peer name when calling over ssh")
    file_command.add_argument(
        "--reply-host",
        help="when calling over ssh: the ssh alias this machine uses to reach yours",
    )
    file_command.set_defaults(handler=command_file)

    check_command = commands.add_parser(
        "check",
        help="check HEARTBEAT.md from stdin against the template, publish nothing",
    )
    check_command.set_defaults(handler=command_check)

    show_command = commands.add_parser("show", help="render one published heartbeat")
    show_command.add_argument("name", help="session name printed by status or file")
    show_command.add_argument("--json", action="store_true")
    show_command.set_defaults(handler=command_show)


def previous_state(directory: Path, name: str) -> str | None:
    try:
        return load_record(directory, name)["state"]
    except InvalidPeerDocument:
        return None


def indexed_entry(orchestrator: str, author: HeartbeatAuthor, heartbeat: dict) -> dict:
    placement = SessionPlacement(
        author.requester_host,
        author.requester_pane,
        frozenset({author.requester, author.requester_pane or ""}),
    )
    entry = filer_entry(entries_of(orchestrator), placement)
    return entry or new_entry(author.name, orchestrator, placement, heartbeat["goal"])


def command_file(arguments: argparse.Namespace, directory: Path) -> int:
    require_unreleased_filer()
    heartbeat = parsed_heartbeat(sys.stdin.read())
    requester = sender_name(arguments.sender)
    pane = os.environ.get("HERDR_PANE_ID")
    name = heartbeat_name(" ".join(filter(None, [requester, pane])))
    author = HeartbeatAuthor(name, requester, pane, arguments.reply_host, arguments.to)
    entry = indexed_entry(arguments.to, author, heartbeat)
    author = replace(author, name=entry["name"])
    record = published_heartbeat(
        heartbeat, author, previous_state(directory, author.name)
    )
    saved_path = save_record(directory, author.name, record)
    if entry.get("heartbeat") != str(saved_path):
        save_entry(entry, saved_path)
    print(entry["name"])
    if not needs_orchestrator_attention(record):
        return 0
    return notify_after_save(
        lambda: requester,
        PeerAddress(arguments.to),
        notification_text(record),
        saved_path,
    )


def command_check(arguments: argparse.Namespace, directory: Path) -> int:
    parsed_heartbeat(sys.stdin.read())
    print("the heartbeat matches the template")
    return 0


def command_show(arguments: argparse.Namespace, directory: Path) -> int:
    record = load_record(directory, heartbeat_name(arguments.name))
    print(
        json.dumps(record, indent=2, ensure_ascii=False)
        if arguments.json
        else rendered_record(record)
    )
    return 0


def command_heartbeat(arguments: argparse.Namespace) -> int:
    try:
        return arguments.handler(arguments, Path(arguments.dir))
    except (InvalidPeerDocument, PeerMessageFailure, SessionReleased) as failure:
        print(f"orchestrator heartbeat: {failure}", file=sys.stderr)
        return 1
