from __future__ import annotations

import secrets
from datetime import datetime, timezone

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


class InvalidDecisionCard(Exception):
    pass


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_decision_identifier() -> str:
    return f"D-{datetime.now(timezone.utc):%Y%m%d}-{secrets.token_hex(3)}"


def nonempty_text(document: dict, field: str) -> str:
    value = document.get(field)
    if not is_nonempty_text(value):
        raise InvalidDecisionCard(f"{field} must be nonempty text")
    return value.strip()


def option_list(document: dict) -> list:
    options = document.get("options")
    if not isinstance(options, list):
        raise InvalidDecisionCard("options must be a list")
    if not MINIMUM_OPTION_COUNT <= len(options) <= MAXIMUM_OPTION_COUNT:
        raise InvalidDecisionCard(
            f"options must list {MINIMUM_OPTION_COUNT} to {MAXIMUM_OPTION_COUNT} choices"
        )
    return options


def validated_option(option) -> dict:
    if not isinstance(option, dict):
        raise InvalidDecisionCard("each option needs a label and a consequence")
    return {
        "label": nonempty_text(option, "label"),
        "consequence": nonempty_text(option, "consequence"),
    }


def validated_options(document: dict) -> list[dict]:
    validated = [validated_option(option) for option in option_list(document)]
    labels = [option["label"] for option in validated]
    if len(set(labels)) != len(labels):
        raise InvalidDecisionCard("option labels must be distinct")
    return validated


def is_nonempty_text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def text_items(value, field: str) -> list[str]:
    if not isinstance(value, list) or not all(map(is_nonempty_text, value)):
        raise InvalidDecisionCard(f"{field} must be a list of nonempty text")
    return [item.strip() for item in value]


def required_text_items(document: dict, field: str) -> list[str]:
    items = text_items(document.get(field), field)
    if not items:
        raise InvalidDecisionCard(f"{field} must list at least one item")
    return items


def new_decision_card(
    document: dict, requester: str, requester_pane: str | None, orchestrator: str
) -> dict:
    if not isinstance(document, dict):
        raise InvalidDecisionCard("the card must be a JSON object")
    card = {field: nonempty_text(document, field) for field in REQUIRED_TEXT_FIELDS}
    card["options"] = validated_options(document)
    if card["recommendation"] not in {option["label"] for option in card["options"]}:
        raise InvalidDecisionCard("recommendation must name one of the option labels")
    card["evidence"] = required_text_items(document, "evidence")
    card["unverified_assumptions"] = text_items(
        document.get("unverified_assumptions", []), "unverified_assumptions"
    )
    if not isinstance(document.get("reversible"), bool):
        raise InvalidDecisionCard("reversible must be true or false")
    card["reversible"] = document["reversible"]
    goal = document.get("goal")
    if goal is not None:
        card["goal"] = nonempty_text(document, "goal")
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
        raise InvalidDecisionCard(f"decision {card['id']} is already {card['state']}")


def answered_card(card: dict, choice: str, rationale: str, decided_by: str) -> dict:
    require_open(card)
    if decided_by not in DECIDERS:
        raise InvalidDecisionCard(f"decided_by must be one of {', '.join(DECIDERS)}")
    if not choice.strip() or not rationale.strip():
        raise InvalidDecisionCard("an answer needs a choice and a rationale")
    return {
        **card,
        "state": ANSWERED_STATE,
        "answer": {
            "choice": choice.strip(),
            "rationale": rationale.strip(),
            "decided_by": decided_by,
            "decided_at": current_timestamp(),
        },
    }


def withdrawn_card(card: dict, reason: str) -> dict:
    require_open(card)
    if not reason.strip():
        raise InvalidDecisionCard("a withdrawal needs a reason")
    return {
        **card,
        "state": WITHDRAWN_STATE,
        "withdrawal": {"reason": reason.strip(), "withdrawn_at": current_timestamp()},
    }
