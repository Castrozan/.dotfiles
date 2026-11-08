from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from ..peer_identity import with_peer_identities
from ..peer_transport import (
    PeerRequestFailure,
    notify_peer,
    read_agent_directory,
    resolve_peer_endpoint,
)
from ..sender_identity import resolve_sender_name, validated_sender_name
from .cards import (
    DECIDERS,
    InvalidDecisionCard,
    answered_card,
    new_decision_card,
    withdrawn_card,
)
from .rendering import notification_text, rendered_card, summary_row
from .store import all_cards, default_decision_directory, load_card, save_card

LISTABLE_STATES = ("open", "answered", "withdrawn", "all")
CARD_FIELDS_DESCRIPTION = (
    "card JSON fields: question, blocked_work, options (2 to 4 objects with label and "
    "consequence), recommendation (one option label), reasoning, evidence (list of "
    "path:line, links, commits or command results), reversible (true or false), "
    "blast_radius; optional goal and unverified_assumptions (list)"
)


def add_parser(subcommands) -> None:
    decision = subcommands.add_parser(
        "decision",
        help="decision cards a peer files for its orchestrator instead of asking the human",
    )
    decision.add_argument("--dir", default=str(default_decision_directory()))
    commands = decision.add_subparsers(dest="decision_command", required=True)

    file_command = commands.add_parser(
        "file",
        help="file a card from JSON and notify the orchestrator",
        epilog=CARD_FIELDS_DESCRIPTION,
    )
    file_command.add_argument("--to", required=True, help="orchestrator peer target")
    file_command.add_argument("--card", default="-", help="JSON file, or - for stdin")
    file_command.add_argument("--sender", help="requester name when calling over ssh")
    file_command.set_defaults(handler=command_file)

    list_command = commands.add_parser("list", help="one row per card")
    list_command.add_argument("--state", choices=LISTABLE_STATES, default="open")
    list_command.add_argument("--for", dest="orchestrator", help="orchestrator name")
    list_command.set_defaults(handler=command_list)

    show_command = commands.add_parser("show", help="render one card for a decider")
    show_command.add_argument("identifier")
    show_command.add_argument("--json", action="store_true")
    show_command.set_defaults(handler=command_show)

    answer_command = commands.add_parser(
        "answer", help="record the decision and notify the requester"
    )
    answer_command.add_argument("identifier")
    answer_command.add_argument("--choice", required=True)
    answer_command.add_argument("--rationale", required=True)
    answer_command.add_argument("--by", required=True, choices=DECIDERS)
    answer_command.add_argument("--sender", help="decider name when calling over ssh")
    answer_command.set_defaults(handler=command_answer)

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
    except (InvalidDecisionCard, PeerRequestFailure) as failure:
        print(f"a2a decision: {failure}", file=sys.stderr)
        return 1


def sender_and_directory(arguments: argparse.Namespace) -> tuple[str, dict]:
    agent_directory = with_peer_identities(read_agent_directory(arguments.daemon))
    if arguments.sender:
        return validated_sender_name(arguments.sender), agent_directory
    return resolve_sender_name(agent_directory), agent_directory


def notify_target(
    agent_directory: dict, target: str, sender: str, card: dict, saved_path: Path
) -> int:
    try:
        notify_peer(
            resolve_peer_endpoint(agent_directory, target),
            sender,
            notification_text(card),
        )
    except PeerRequestFailure as failure:
        print(
            f"a2a decision: {card['id']} is saved at {saved_path} but {target} was not "
            f"notified: {failure}",
            file=sys.stderr,
        )
        return 1
    return 0


def read_card_document(card_source: str) -> dict:
    raw_text = (
        sys.stdin.read()
        if card_source == "-"
        else Path(card_source).read_text(encoding="utf-8")
    )
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as failure:
        raise InvalidDecisionCard(f"the card is not valid JSON: {failure}") from failure


def command_file(arguments: argparse.Namespace, decision_directory: Path) -> int:
    document = read_card_document(arguments.card)
    requester, agent_directory = sender_and_directory(arguments)
    card = new_decision_card(
        document, requester, os.environ.get("HERDR_PANE_ID"), arguments.to
    )
    saved_path = save_card(decision_directory, card)
    print(card["id"])
    return notify_target(agent_directory, arguments.to, requester, card, saved_path)


def command_list(arguments: argparse.Namespace, decision_directory: Path) -> int:
    for card in all_cards(decision_directory):
        if arguments.state != "all" and card["state"] != arguments.state:
            continue
        if arguments.orchestrator and card["orchestrator"] != arguments.orchestrator:
            continue
        print(summary_row(card))
    return 0


def command_show(arguments: argparse.Namespace, decision_directory: Path) -> int:
    card = load_card(decision_directory, arguments.identifier)
    print(
        json.dumps(card, indent=2, ensure_ascii=False)
        if arguments.json
        else rendered_card(card)
    )
    return 0


def command_answer(arguments: argparse.Namespace, decision_directory: Path) -> int:
    card = answered_card(
        load_card(decision_directory, arguments.identifier),
        arguments.choice,
        arguments.rationale,
        arguments.by,
    )
    decider, agent_directory = sender_and_directory(arguments)
    saved_path = save_card(decision_directory, card)
    requester_target = card["requester_pane"] or card["requester"]
    return notify_target(agent_directory, requester_target, decider, card, saved_path)


def command_withdraw(arguments: argparse.Namespace, decision_directory: Path) -> int:
    card = withdrawn_card(
        load_card(decision_directory, arguments.identifier), arguments.reason
    )
    requester, agent_directory = sender_and_directory(arguments)
    saved_path = save_card(decision_directory, card)
    return notify_target(
        agent_directory, card["orchestrator"], requester, card, saved_path
    )
