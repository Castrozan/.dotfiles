from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..document_fields import InvalidPeerDocument
from ..peer_transport import PeerRequestFailure
from ..record_store import state_directory
from .cards import DECIDERS
from .delegation import HUMAN_ONLY_REASONS
from .handlers import (
    command_answer,
    command_file,
    command_list,
    command_show,
    command_withdraw,
)

LISTABLE_STATES = ("open", "answered", "withdrawn", "all")
CARD_FIELDS_DESCRIPTION = (
    "card JSON fields: question, blocked_work, options (2 to 4 objects with label and "
    "consequence), recommendation (one option label), reasoning, evidence (list of "
    "path:line, links, commits or command results), reversible (true or false), "
    "blast_radius; optional goal, unverified_assumptions (list), human_only (list of "
    f"{', '.join(HUMAN_ONLY_REASONS)})"
)


def add_file_parser(commands) -> None:
    file_command = commands.add_parser(
        "file",
        help="file a card from JSON and notify the orchestrator",
        epilog=CARD_FIELDS_DESCRIPTION,
    )
    file_command.add_argument("--to", required=True, help="orchestrator peer target")
    file_command.add_argument("--card", default="-", help="JSON file, or - for stdin")
    file_command.add_argument("--sender", help="requester name when calling over ssh")
    file_command.set_defaults(handler=command_file)


def add_list_parser(commands) -> None:
    list_command = commands.add_parser("list", help="one row per card")
    list_command.add_argument("--state", choices=LISTABLE_STATES, default="open")
    list_command.add_argument("--for", dest="orchestrator", help="orchestrator name")
    list_command.add_argument("--decided-by", choices=DECIDERS)
    list_command.add_argument("--since-hours", type=float)
    list_command.set_defaults(handler=command_list)


def add_answer_parser(commands) -> None:
    answer_command = commands.add_parser(
        "answer", help="record the decision and notify the requester"
    )
    answer_command.add_argument("identifier")
    answer_command.add_argument("--choice", required=True)
    answer_command.add_argument("--rationale", required=True)
    answer_command.add_argument("--by", required=True, choices=DECIDERS)
    answer_command.add_argument("--sender", help="decider name when calling over ssh")
    answer_command.set_defaults(handler=command_answer)


def add_parser(subcommands) -> None:
    decision = subcommands.add_parser(
        "decision",
        help="decision cards a peer files for its orchestrator instead of asking the human",
    )
    decision.add_argument("--dir", default=str(state_directory("a2a-decisions")))
    commands = decision.add_subparsers(dest="decision_command", required=True)
    add_file_parser(commands)
    add_list_parser(commands)
    add_answer_parser(commands)

    show_command = commands.add_parser("show", help="render one card for a decider")
    show_command.add_argument("identifier")
    show_command.add_argument("--json", action="store_true")
    show_command.set_defaults(handler=command_show)

    withdraw_command = commands.add_parser(
        "withdraw", help="close a card that no longer needs a decision"
    )
    withdraw_command.add_argument("identifier")
    withdraw_command.add_argument("--reason", required=True)
    withdraw_command.add_argument(
        "--sender", help="requester name when calling over ssh"
    )
    withdraw_command.set_defaults(handler=command_withdraw)


def command_decision(arguments: argparse.Namespace) -> int:
    try:
        return arguments.handler(arguments, Path(arguments.dir))
    except (InvalidPeerDocument, PeerRequestFailure) as failure:
        print(f"a2a decision: {failure}", file=sys.stderr)
        return 1
