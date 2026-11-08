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
    if not isinstance(value, str) or not value.strip():
        raise InvalidDecisionCard(f"{field} must be nonempty text")
    return value.strip()


def validated_options(document: dict) -> list[dict]:
    options = document.get("options")
    if not isinstance(options, list) or not (
        MINIMUM_OPTION_COUNT <= len(options) <= MAXIMUM_OPTION_COUNT
    ):
        raise InvalidDecisionCard(
            f"options must list {MINIMUM_OPTION_COUNT} to {MAXIMUM_OPTION_COUNT} choices"
        )
    validated = []
    for option in options:
        if not isinstance(option, dict):
            raise InvalidDecisionCard("each option needs a label and a consequence")
        validated.append(
            {
                "label": nonempty_text(option, "label"),
                "consequence": nonempty_text(option, "consequence"),
            }
        )
    labels = [option["label"] for option in validated]
    if len(set(labels)) != len(labels):
        raise InvalidDecisionCard("option labels must be distinct")
    return validated


def validated_text_list(document: dict, field: str, required: bool) -> list[str]:
    items = document.get(field, None if required else [])
    if not isinstance(items, list) or (required and not items):
        raise InvalidDecisionCard(f"{field} must list at least one item")
    if not all(isinstance(item, str) and item.strip() for item in items):
        raise InvalidDecisionCard(f"every {field} item must be nonempty text")
    return [item.strip() for item in items]


def new_decision_card(
    document: dict, requester: str, requester_pane: str | None, orchestrator: str
) -> dict:
    if not isinstance(document, dict):
        raise InvalidDecisionCard("the card must be a JSON object")
    card = {field: nonempty_text(document, field) for field in REQUIRED_TEXT_FIELDS}
    card["options"] = validated_options(document)
    if card["recommendation"] not in {option["label"] for option in card["options"]}:
        raise InvalidDecisionCard("recommendation must name one of the option labels")
    card["evidence"] = validated_text_list(document, "evidence", required=True)
    card["unverified_assumptions"] = validated_text_list(
        document, "unverified_assumptions", required=False
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
