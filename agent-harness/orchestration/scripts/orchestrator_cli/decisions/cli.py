from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ..document_fields import InvalidPeerDocument
from ..peer_messenger import PeerMessageFailure
from ..record_store import state_directory
from ..user_model.directives import default_user_model_path
from .cards import DECIDERS, ESCALATION_REASONS
from .delegation import HUMAN_ONLY_REASONS
from .handlers import (
    command_answer,
    command_escalate,
    command_file,
    command_link,
    command_list,
    command_override,
    command_show,
    command_withdraw,
)

LISTABLE_STATES = ("open", "escalated", "answered", "overridden", "withdrawn", "all")
CARD_FIELDS_DESCRIPTION = (
    "card JSON fields: goal (what this session is for), progress (what it has "
    "established so far), question, blocked_work, options (2 to 4 objects with label "
    "and consequence), recommendation (one option label), reasoning, evidence (list of "
    "path:line, links, commits or command results), reversible (true or false), "
    "blast_radius; optional unverified_assumptions (list), details (absolute path of "
    "a file holding tables and long material) and human_only (list of "
    f"{', '.join(HUMAN_ONLY_REASONS)}). Every text field is one line and bounded so "
    "the card fits one reply; the refusal names the field and its limit"
)


def add_sender_argument(command) -> None:
    command.add_argument("--sender", help="your name when calling over ssh")


def add_file_parser(commands) -> None:
    file_command = commands.add_parser(
        "file",
        help="file a card from JSON and notify the orchestrator",
        epilog=CARD_FIELDS_DESCRIPTION,
    )
    file_command.add_argument("--to", required=True, help="orchestrator peer target")
    file_command.add_argument("--card", default="-", help="JSON file, or - for stdin")
    add_sender_argument(file_command)
    file_command.set_defaults(handler=command_file)


def add_list_parser(commands) -> None:
    list_command = commands.add_parser("list", help="one row per card")
    list_command.add_argument("--state", choices=LISTABLE_STATES, default="open")
    list_command.add_argument("--for", dest="orchestrator", help="orchestrator name")
    list_command.add_argument("--decided-by", choices=DECIDERS)
    list_command.add_argument("--since-hours", type=float)
    list_command.set_defaults(handler=command_list)


def add_answer_parsers(commands) -> None:
    answer_command = commands.add_parser(
        "answer", help="record the decision and notify the requester"
    )
    answer_command.add_argument("identifier")
    answer_command.add_argument("--choice", required=True)
    answer_command.add_argument("--rationale", required=True)
    answer_command.add_argument("--by", required=True, choices=DECIDERS)
    answer_command.add_argument("--directive", help="USER.md directive id it applies")
    answer_command.add_argument("--user-model", default=str(default_user_model_path()))
    add_sender_argument(answer_command)
    answer_command.set_defaults(handler=command_answer)

    override_command = commands.add_parser(
        "override", help="the human countermands a decision; notifies the requester"
    )
    override_command.add_argument("identifier")
    override_command.add_argument("--choice", required=True)
    override_command.add_argument(
        "--rationale", required=True, help="the human's words"
    )
    add_sender_argument(override_command)
    override_command.set_defaults(handler=command_override)


def add_lifecycle_parsers(commands) -> None:
    escalate_command = commands.add_parser(
        "escalate", help="the orchestrator hands the card to the human, saying why"
    )
    escalate_command.add_argument("identifier")
    escalate_command.add_argument("--reason", required=True, choices=ESCALATION_REASONS)
    escalate_command.add_argument(
        "--missing", required=True, help="what USER.md would need to decide this"
    )
    escalate_command.set_defaults(handler=command_escalate)

    withdraw_command = commands.add_parser(
        "withdraw", help="close a card that no longer needs a decision"
    )
    withdraw_command.add_argument("identifier")
    withdraw_command.add_argument("--reason", required=True)
    add_sender_argument(withdraw_command)
    withdraw_command.set_defaults(handler=command_withdraw)

    link_command = commands.add_parser(
        "link", help="record the commits that carried out a decision"
    )
    link_command.add_argument("identifier")
    link_command.add_argument("--repository", required=True)
    link_command.add_argument("commits", nargs="+")
    link_command.set_defaults(handler=command_link)


def add_parser(subcommands) -> None:
    decision = subcommands.add_parser(
        "decision",
        help="decision cards a peer files for its orchestrator instead of asking the human",
    )
    decision.add_argument(
        "--dir", default=str(state_directory("orchestrator-decisions"))
    )
    commands = decision.add_subparsers(dest="decision_command", required=True)
    add_file_parser(commands)
    add_list_parser(commands)
    add_answer_parsers(commands)
    add_lifecycle_parsers(commands)
    show_command = commands.add_parser("show", help="the card in the human template")
    show_command.add_argument("identifier")
    show_command.add_argument("--json", action="store_true")
    show_command.set_defaults(handler=command_show)


def command_decision(arguments: argparse.Namespace) -> int:
    try:
        return arguments.handler(arguments, Path(arguments.dir))
    except (InvalidPeerDocument, PeerMessageFailure) as failure:
        print(f"orchestrator decision: {failure}", file=sys.stderr)
        return 1
