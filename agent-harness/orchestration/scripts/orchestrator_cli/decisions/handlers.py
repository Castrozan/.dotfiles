from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..document_fields import InvalidPeerDocument
from ..peer_messenger import notify_after_save, sender_name
from ..record_store import all_records, load_record, save_record
from ..user_model.directives import active_identifiers
from .cards import (
    answered_card,
    card_with_work,
    escalated_card,
    new_decision_card,
    overridden_card,
    withdrawn_card,
)
from .delegation import require_orchestrator_authority
from .rendering import notification_text, rendered_card, summary_row


def all_cards(decision_directory: Path) -> list[dict]:
    return sorted(all_records(decision_directory), key=lambda card: card["created_at"])


def read_card_document(card_source: str):
    raw_text = (
        sys.stdin.read()
        if card_source == "-"
        else Path(card_source).read_text(encoding="utf-8")
    )
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as failure:
        raise InvalidPeerDocument(f"the card is not valid JSON: {failure}") from failure


def save_and_notify(
    arguments: argparse.Namespace, decision_directory: Path, card: dict, target: str
) -> int:
    saved_path = save_record(decision_directory, card["id"], card)
    return notify_after_save(
        lambda: sender_name(arguments.sender),
        target,
        notification_text(card),
        saved_path,
    )


def requester_target(card: dict) -> str:
    return card["requester_pane"] or card["requester"]


def command_file(arguments: argparse.Namespace, decision_directory: Path) -> int:
    document = read_card_document(arguments.card)
    requester = sender_name(arguments.sender)
    card = new_decision_card(
        document, requester, os.environ.get("HERDR_PANE_ID"), arguments.to
    )
    saved_path = save_record(decision_directory, card["id"], card)
    print(card["id"])
    return notify_after_save(
        lambda: requester,
        arguments.to,
        notification_text(card),
        saved_path,
    )


def last_change(card: dict) -> str:
    return card.get("answer", {}).get("decided_at", card["created_at"])


def card_matches(card: dict, arguments: argparse.Namespace, cutoff: str) -> bool:
    filters = (
        arguments.state in ("all", card["state"]),
        arguments.orchestrator in (None, card["orchestrator"]),
        arguments.decided_by in (None, card.get("answer", {}).get("decided_by")),
    )
    return all(filters) and last_change(card) >= cutoff


def command_list(arguments: argparse.Namespace, decision_directory: Path) -> int:
    cutoff = ""
    if arguments.since_hours is not None:
        since = datetime.now(timezone.utc) - timedelta(hours=arguments.since_hours)
        cutoff = since.isoformat(timespec="seconds")
    for card in all_cards(decision_directory):
        if card_matches(card, arguments, cutoff):
            print(summary_row(card))
    return 0


def command_show(arguments: argparse.Namespace, decision_directory: Path) -> int:
    card = load_record(decision_directory, arguments.identifier)
    print(
        json.dumps(card, indent=2, ensure_ascii=False)
        if arguments.json
        else rendered_card(card)
    )
    return 0


def command_escalate(arguments: argparse.Namespace, decision_directory: Path) -> int:
    card = escalated_card(
        load_record(decision_directory, arguments.identifier),
        arguments.reason,
        arguments.missing,
    )
    save_record(decision_directory, card["id"], card)
    print(rendered_card(card))
    return 0


def command_answer(arguments: argparse.Namespace, decision_directory: Path) -> int:
    card = load_record(decision_directory, arguments.identifier)
    if arguments.by == "orchestrator":
        directives = active_identifiers(Path(arguments.user_model))
        require_orchestrator_authority(card, arguments.directive, directives)
    elif arguments.directive:
        raise InvalidPeerDocument("--directive applies only to orchestrator decisions")
    card = answered_card(
        card, arguments.choice, arguments.rationale, arguments.by, arguments.directive
    )
    return save_and_notify(arguments, decision_directory, card, requester_target(card))


def command_override(arguments: argparse.Namespace, decision_directory: Path) -> int:
    card = overridden_card(
        load_record(decision_directory, arguments.identifier),
        arguments.choice,
        arguments.rationale,
    )
    return save_and_notify(arguments, decision_directory, card, requester_target(card))


def command_withdraw(arguments: argparse.Namespace, decision_directory: Path) -> int:
    card = withdrawn_card(
        load_record(decision_directory, arguments.identifier), arguments.reason
    )
    return save_and_notify(arguments, decision_directory, card, card["orchestrator"])


def command_link(arguments: argparse.Namespace, decision_directory: Path) -> int:
    repository = str(Path(arguments.repository).expanduser().resolve())
    card = card_with_work(
        load_record(decision_directory, arguments.identifier),
        repository,
        arguments.commits,
    )
    save_record(decision_directory, card["id"], card)
    return 0
