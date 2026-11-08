from __future__ import annotations

from ..document_fields import InvalidPeerDocument

CARD_TEXT_LIMITS = {
    "goal": 200,
    "progress": 800,
    "question": 200,
    "blocked_work": 200,
    "recommendation": 60,
    "reasoning": 500,
    "blast_radius": 250,
    "details": 300,
}
OPTION_TEXT_LIMITS = {"label": 60, "consequence": 200}
CARD_LIST_LIMITS = {"evidence": 8, "unverified_assumptions": 4}
LIST_ITEM_LIMIT = 160
ESCALATION_MISSING_LIMIT = 300
OVERFLOW_ADVICE = "put tables and long material in a file and name it in details"


def require_relayable_text(field: str, value: str, limit: int) -> None:
    if "\n" in value:
        raise InvalidPeerDocument(f"{field} must be one line; {OVERFLOW_ADVICE}")
    if len(value) > limit:
        raise InvalidPeerDocument(
            f"{field} is {len(value)} characters, over its limit of {limit}; "
            f"{OVERFLOW_ADVICE}"
        )


def require_relayable_list(card: dict, field: str, maximum_items: int) -> None:
    if len(card[field]) > maximum_items:
        raise InvalidPeerDocument(
            f"{field} lists {len(card[field])} items, over its limit of {maximum_items}; "
            f"{OVERFLOW_ADVICE}"
        )
    for item in card[field]:
        require_relayable_text(field, item, LIST_ITEM_LIMIT)


def require_relayable_option(option: dict) -> None:
    for field, limit in OPTION_TEXT_LIMITS.items():
        require_relayable_text(f"option {field}", option[field], limit)


def require_relayable_card(card: dict) -> None:
    for field, limit in CARD_TEXT_LIMITS.items():
        if field in card:
            require_relayable_text(field, card[field], limit)
    for option in card["options"]:
        require_relayable_option(option)
    for field, maximum_items in CARD_LIST_LIMITS.items():
        require_relayable_list(card, field, maximum_items)
