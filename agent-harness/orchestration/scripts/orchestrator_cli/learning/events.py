from __future__ import annotations

from collections import Counter

from ..document_fields import InvalidPeerDocument, current_timestamp

LEARNING_OUTCOMES = ("added", "superseded", "no-change")


def decided_by(card: dict, decider: str) -> bool:
    return card.get("answer", {}).get("decided_by") == decider


def escalation_answered_by_human(card: dict) -> bool:
    return (
        card["state"] == "answered"
        and "escalation" in card
        and decided_by(card, "human")
    )


def learning_event_kind(card: dict) -> str | None:
    if "learning" in card:
        return None
    kinds = (
        ("override", card["state"] == "overridden"),
        ("escalation", escalation_answered_by_human(card)),
        ("deviation", bool(card.get("deviations"))),
    )
    return next((kind for kind, applies in kinds if applies), None)


def pending_learning_events(cards: list[dict]) -> list[tuple[str, dict]]:
    events = [(learning_event_kind(card), card) for card in cards]
    return [(kind, card) for kind, card in events if kind]


def learned_card(card: dict, outcome: str, directive: str | None, reason: str) -> dict:
    if learning_event_kind(card) is None:
        raise InvalidPeerDocument(f"decision {card['id']} has nothing pending to learn")
    if outcome not in LEARNING_OUTCOMES:
        raise InvalidPeerDocument(
            f"outcome must be one of {', '.join(LEARNING_OUTCOMES)}"
        )
    if (outcome == "no-change") == bool(directive):
        raise InvalidPeerDocument(
            "added and superseded name the resulting directive; no-change names none"
        )
    if not reason.strip():
        raise InvalidPeerDocument(
            "a learning outcome needs the inferred preference or why none"
        )
    learning = {
        "outcome": outcome,
        "directive": directive,
        "reason": reason.strip(),
        "resolved_at": current_timestamp(),
    }
    return {**card, "learning": learning}


def require_directive_cites_card(
    card_identifier: str, directive_identifier: str, directives: list
) -> None:
    directive = next(
        (each for each in directives if each.identifier == directive_identifier), None
    )
    if directive is None or not directive.active:
        raise InvalidPeerDocument(
            f"{directive_identifier} is not an active directive in the user model"
        )
    if card_identifier not in directive.source:
        raise InvalidPeerDocument(
            f"{directive_identifier} must cite {card_identifier} as its source"
        )


def deviation_candidates(
    card: dict, linked_commits: set[str], changed_since
) -> list[str]:
    if "learning" in card or card["state"] != "answered":
        return []
    if not decided_by(card, "orchestrator") or "work" not in card:
        return []
    work = card["work"]
    later_commits = changed_since(work["repository"], work["commits"])
    return [commit for commit in later_commits if commit not in linked_commits]


def learning_statistics(cards: list[dict]) -> dict:
    states = Counter(card["state"] for card in cards)
    escalation_reasons = Counter(
        card["escalation"]["reason"] for card in cards if "escalation" in card
    )
    return {
        "cards": len(cards),
        "decided_by_orchestrator": sum(
            decided_by(card, "orchestrator") for card in cards
        ),
        "decided_by_human": sum(decided_by(card, "human") for card in cards),
        "escalated": dict(escalation_reasons),
        "overridden": states["overridden"],
        "deviations": sum(bool(card.get("deviations")) for card in cards),
        "pending_learning": len(pending_learning_events(cards)),
        "open": states["open"] + states["escalated"],
    }
