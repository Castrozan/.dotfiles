from __future__ import annotations

import secrets
from datetime import datetime, timezone

from ..document_fields import (
    InvalidPeerDocument,
    current_timestamp,
    nonempty_text,
    optional_text_items,
    require_object,
    required_text_items,
)
from .delegation import validated_human_only

OPEN_STATE = "open"
ANSWERED_STATE = "answered"
WITHDRAWN_STATE = "withdrawn"
DECIDERS = ("human", "orchestrator")
MINIMUM_OPTION_COUNT = 2
MAXIMUM_OPTION_COUNT = 4
REQUIRED_TEXT_FIELDS = (
    "question",
    "blocked_work",
    "recommendation",
    "reasoning",
    "blast_radius",
)


def new_decision_identifier() -> str:
    return f"D-{datetime.now(timezone.utc):%Y%m%d}-{secrets.token_hex(3)}"


def option_list(document: dict) -> list:
    options = document.get("options")
    if not isinstance(options, list):
        raise InvalidPeerDocument("options must be a list")
    if not MINIMUM_OPTION_COUNT <= len(options) <= MAXIMUM_OPTION_COUNT:
        raise InvalidPeerDocument(
            f"options must list {MINIMUM_OPTION_COUNT} to {MAXIMUM_OPTION_COUNT} choices"
        )
    return options


def validated_option(option) -> dict:
    option = require_object(option, "each option")
    return {
        "label": nonempty_text(option, "label"),
        "consequence": nonempty_text(option, "consequence"),
    }


def validated_options(document: dict) -> list[dict]:
    validated = [validated_option(option) for option in option_list(document)]
    labels = [option["label"] for option in validated]
    if len(set(labels)) != len(labels):
        raise InvalidPeerDocument("option labels must be distinct")
    return validated


def validated_card_fields(document: dict) -> dict:
    card = {field: nonempty_text(document, field) for field in REQUIRED_TEXT_FIELDS}
    card["options"] = validated_options(document)
    if card["recommendation"] not in {option["label"] for option in card["options"]}:
        raise InvalidPeerDocument("recommendation must name one of the option labels")
    card["evidence"] = required_text_items(document, "evidence")
    card["unverified_assumptions"] = optional_text_items(
        document, "unverified_assumptions"
    )
    if not isinstance(document.get("reversible"), bool):
        raise InvalidPeerDocument("reversible must be true or false")
    card["reversible"] = document["reversible"]
    if "goal" in document:
        card["goal"] = nonempty_text(document, "goal")
    return card


def new_decision_card(
    document, requester: str, requester_pane: str | None, orchestrator: str
) -> dict:
    document = require_object(document, "the card")
    card = validated_card_fields(document)
    card["human_only"] = validated_human_only(document)
    return {
        "id": new_decision_identifier(),
        "state": OPEN_STATE,
        "created_at": current_timestamp(),
        "requester": requester,
        "requester_pane": requester_pane,
        "orchestrator": orchestrator,
        **card,
    }


def require_open(card: dict) -> None:
    if card["state"] != OPEN_STATE:
        raise InvalidPeerDocument(f"decision {card['id']} is already {card['state']}")


def answered_card(card: dict, choice: str, rationale: str, decided_by: str) -> dict:
    require_open(card)
    if decided_by not in DECIDERS:
        raise InvalidPeerDocument(f"decided_by must be one of {', '.join(DECIDERS)}")
    if not choice.strip() or not rationale.strip():
        raise InvalidPeerDocument("an answer needs a choice and a rationale")
    answer = {
        "choice": choice.strip(),
        "rationale": rationale.strip(),
        "decided_by": decided_by,
        "decided_at": current_timestamp(),
    }
    return {**card, "state": ANSWERED_STATE, "answer": answer}


def withdrawn_card(card: dict, reason: str) -> dict:
    require_open(card)
    if not reason.strip():
        raise InvalidPeerDocument("a withdrawal needs a reason")
    return {
        **card,
        "state": WITHDRAWN_STATE,
        "withdrawal": {"reason": reason.strip(), "withdrawn_at": current_timestamp()},
    }
