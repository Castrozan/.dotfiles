from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from ..document_fields import InvalidPeerDocument
from ..peer_messenger import PeerMessageFailure, notify_after_save, sender_name
from ..record_store import all_records, load_record, save_record, state_directory
from .status_reports import (
    REPORT_STATES,
    ReportAuthor,
    needs_orchestrator_attention,
    new_status_report,
    notification_text,
    rendered_report,
    report_name,
    summary_row,
)

REPORT_FIELDS_DESCRIPTION = (
    "report JSON fields: goal, state (" + ", ".join(REPORT_STATES) + "), done_check, "
    "progress, next_step; optional verified (list of objects with claim and evidence), "
    "unverified (list) and open_decisions (list of decision ids)"
)


def add_parser(subcommands) -> None:
    report = subcommands.add_parser(
        "report", help="a peer's current status for its orchestrator, one per peer"
    )
    report.add_argument("--dir", default=str(state_directory("orchestrator-reports")))
    commands = report.add_subparsers(dest="report_command", required=True)

    file_command = commands.add_parser(
        "file",
        help="replace this peer's report; notifies only on turning blocked or done",
        epilog=REPORT_FIELDS_DESCRIPTION,
    )
    file_command.add_argument("--to", required=True, help="orchestrator peer target")
    file_command.add_argument("--report", default="-", help="JSON file, or - for stdin")
    file_command.add_argument("--sender", help="peer name when calling over ssh")
    file_command.set_defaults(handler=command_file)

    list_command = commands.add_parser("list", help="one row per peer report")
    list_command.add_argument("--for", dest="orchestrator", help="orchestrator name")
    list_command.set_defaults(handler=command_list)

    show_command = commands.add_parser("show", help="render one peer's report")
    show_command.add_argument("name", help="report name printed by list or file")
    show_command.add_argument("--json", action="store_true")
    show_command.set_defaults(handler=command_show)


def read_report_document(report_source: str):
    raw_text = (
        sys.stdin.read()
        if report_source == "-"
        else Path(report_source).read_text(encoding="utf-8")
    )
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as failure:
        raise InvalidPeerDocument(
            f"the report is not valid JSON: {failure}"
        ) from failure


def previous_state(report_directory: Path, name: str) -> str | None:
    try:
        return load_record(report_directory, name)["state"]
    except InvalidPeerDocument:
        return None


def command_file(arguments: argparse.Namespace, report_directory: Path) -> int:
    document = read_report_document(arguments.report)
    requester = sender_name(arguments.sender)
    requester_pane = os.environ.get("HERDR_PANE_ID")
    name = report_name(" ".join(filter(None, [requester, requester_pane])))
    author = ReportAuthor(name, requester, requester_pane, arguments.to)
    report = new_status_report(document, author, previous_state(report_directory, name))
    saved_path = save_record(report_directory, name, report)
    print(name)
    if not needs_orchestrator_attention(report):
        return 0
    return notify_after_save(
        lambda: requester,
        arguments.to,
        notification_text(report),
        saved_path,
    )


def command_list(arguments: argparse.Namespace, report_directory: Path) -> int:
    for report in sorted(all_records(report_directory), key=lambda r: r["updated_at"]):
        if arguments.orchestrator in (None, report["orchestrator"]):
            print(summary_row(report))
    return 0


def command_show(arguments: argparse.Namespace, report_directory: Path) -> int:
    report = load_record(report_directory, report_name(arguments.name))
    print(
        json.dumps(report, indent=2, ensure_ascii=False)
        if arguments.json
        else rendered_report(report)
    )
    return 0


def command_report(arguments: argparse.Namespace) -> int:
    try:
        return arguments.handler(arguments, Path(arguments.dir))
    except (InvalidPeerDocument, PeerMessageFailure) as failure:
        print(f"orchestrator report: {failure}", file=sys.stderr)
        return 1
