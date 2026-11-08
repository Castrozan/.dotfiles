from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..document_fields import InvalidPeerDocument
from ..peer_delivery import notify_after_save, sender_and_directory
from ..record_store import all_records, load_record, save_record
from .cards import answered_card, new_decision_card, withdrawn_card
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


def command_file(arguments: argparse.Namespace, decision_directory: Path) -> int:
    document = read_card_document(arguments.card)
    requester, agent_directory = sender_and_directory(arguments)
    card = new_decision_card(
        document, requester, os.environ.get("HERDR_PANE_ID"), arguments.to
    )
    saved_path = save_record(decision_directory, card["id"], card)
    print(card["id"])
    return notify_after_save(
        lambda: (requester, agent_directory),
        arguments.to,
        notification_text(card),
        saved_path,
    )


def last_change(card: dict) -> str:
    return card["answer"]["decided_at"] if "answer" in card else card["created_at"]


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


def command_answer(arguments: argparse.Namespace, decision_directory: Path) -> int:
    card = load_record(decision_directory, arguments.identifier)
    if arguments.by == "orchestrator":
        require_orchestrator_authority(card)
    card = answered_card(card, arguments.choice, arguments.rationale, arguments.by)
    saved_path = save_record(decision_directory, card["id"], card)
    return notify_after_save(
        lambda: sender_and_directory(arguments),
        card["requester_pane"] or card["requester"],
        notification_text(card),
        saved_path,
    )


def command_withdraw(arguments: argparse.Namespace, decision_directory: Path) -> int:
    card = withdrawn_card(
        load_record(decision_directory, arguments.identifier), arguments.reason
    )
    saved_path = save_record(decision_directory, card["id"], card)
    return notify_after_save(
        lambda: sender_and_directory(arguments),
        card["orchestrator"],
        notification_text(card),
        saved_path,
    )
