from __future__ import annotations

from ..document_fields import InvalidPeerDocument, optional_text_items

HUMAN_ONLY_REASONS = (
    "secret",
    "ril-verdict",
    "goal-launch",
    "herdr-server-activation",
    "outward-publication",
    "money",
    "data-loss",
)


def validated_human_only(document: dict) -> list[str]:
    reasons = optional_text_items(document, "human_only")
    unknown = sorted(set(reasons) - set(HUMAN_ONLY_REASONS))
    if unknown:
        raise InvalidPeerDocument(
            f"human_only accepts {', '.join(HUMAN_ONLY_REASONS)}; got {', '.join(unknown)}"
        )
    return reasons


def human_only_grounds(card: dict) -> list[str]:
    grounds = list(card.get("human_only", []))
    if not card["reversible"]:
        grounds.append("irreversible")
    return grounds


def require_orchestrator_authority(
    card: dict, directive: str | None, active_directives: set[str]
) -> None:
    grounds = human_only_grounds(card)
    if grounds:
        raise InvalidPeerDocument(
            f"decision {card['id']} is the human's: {', '.join(grounds)}"
        )
    if card["state"] != "open":
        raise InvalidPeerDocument(f"decision {card['id']} was escalated to the human")
    if directive not in active_directives:
        raise InvalidPeerDocument(
            "an orchestrator decision must cite an active USER.md directive with --directive"
        )
