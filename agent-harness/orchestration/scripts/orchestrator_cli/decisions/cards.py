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
from .card_limits import (
    ESCALATION_MISSING_LIMIT,
    require_relayable_card,
    require_relayable_text,
)
from .delegation import validated_human_only

OPEN_STATE = "open"
ESCALATED_STATE = "escalated"
ANSWERED_STATE = "answered"
OVERRIDDEN_STATE = "overridden"
WITHDRAWN_STATE = "withdrawn"
DECIDERS = ("human", "orchestrator")
ESCALATION_REASONS = (
    "no-directive",
    "conflicting-directives",
    "human-only",
    "weak-evidence",
)
MINIMUM_OPTION_COUNT = 2
MAXIMUM_OPTION_COUNT = 4
REQUIRED_TEXT_FIELDS = (
    "goal",
    "progress",
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
    card["human_only"] = validated_human_only(document)
    if "details" in document:
        card["details"] = nonempty_text(document, "details")
    require_relayable_card(card)
    return card


def new_decision_card(
    document, requester: str, requester_pane: str | None, orchestrator: str
) -> dict:
    return {
        "id": new_decision_identifier(),
        "state": OPEN_STATE,
        "created_at": current_timestamp(),
        "requester": requester,
        "requester_pane": requester_pane,
        "orchestrator": orchestrator,
        **validated_card_fields(require_object(document, "the card")),
    }


def require_state(card: dict, allowed_states: tuple[str, ...]) -> None:
    if card["state"] not in allowed_states:
        raise InvalidPeerDocument(
            f"decision {card['id']} is {card['state']}; expected {' or '.join(allowed_states)}"
        )


def required_text(value: str, description: str) -> str:
    if not value.strip():
        raise InvalidPeerDocument(f"{description} must be nonempty")
    return value.strip()


def escalated_card(card: dict, reason: str, missing: str) -> dict:
    require_state(card, (OPEN_STATE,))
    if reason not in ESCALATION_REASONS:
        raise InvalidPeerDocument(
            f"reason must be one of {', '.join(ESCALATION_REASONS)}"
        )
    lacking = required_text(missing, "what the user model lacked")
    require_relayable_text("missing", lacking, ESCALATION_MISSING_LIMIT)
    escalation = {
        "reason": reason,
        "missing": lacking,
        "escalated_at": current_timestamp(),
    }
    return {**card, "state": ESCALATED_STATE, "escalation": escalation}


def answered_card(
    card: dict, choice: str, rationale: str, decided_by: str, directive: str | None
) -> dict:
    require_state(card, (OPEN_STATE, ESCALATED_STATE))
    answer = {
        "choice": required_text(choice, "the choice"),
        "rationale": required_text(rationale, "the rationale"),
        "decided_by": decided_by,
        "decided_at": current_timestamp(),
    }
    if directive:
        answer["directive"] = directive
    return {**card, "state": ANSWERED_STATE, "answer": answer}


def overridden_card(card: dict, choice: str, rationale: str) -> dict:
    require_state(card, (ANSWERED_STATE,))
    override = {
        "choice": required_text(choice, "the human's choice"),
        "rationale": required_text(rationale, "the human's words"),
        "overridden_at": current_timestamp(),
    }
    return {**card, "state": OVERRIDDEN_STATE, "override": override}


def withdrawn_card(card: dict, reason: str) -> dict:
    require_state(card, (OPEN_STATE, ESCALATED_STATE))
    withdrawal = {
        "reason": required_text(reason, "a withdrawal reason"),
        "withdrawn_at": current_timestamp(),
    }
    return {**card, "state": WITHDRAWN_STATE, "withdrawal": withdrawal}


def card_with_work(card: dict, repository: str, commits: list[str]) -> dict:
    require_state(card, (ANSWERED_STATE, OVERRIDDEN_STATE))
    work = card.get("work") or {"repository": repository, "commits": []}
    if work["repository"] != repository:
        raise InvalidPeerDocument(
            f"decision {card['id']} work lives in {work['repository']}"
        )
    linked = work["commits"] + [
        commit for commit in commits if commit not in work["commits"]
    ]
    return {**card, "work": {"repository": repository, "commits": linked}}
