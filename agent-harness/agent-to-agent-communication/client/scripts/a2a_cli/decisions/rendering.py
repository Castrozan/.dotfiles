from __future__ import annotations

from .cards import ANSWERED_STATE, WITHDRAWN_STATE


def option_line(option: dict, recommendation: str) -> str:
    marker = " (recommended)" if option["label"] == recommendation else ""
    return f"- **{option['label']}**{marker}: {option['consequence']}"


def assumption_lines(card: dict) -> list[str]:
    assumptions = card.get("unverified_assumptions") or []
    if not assumptions:
        return []
    return ["", "**Unverified assumptions**", *(f"- {item}" for item in assumptions)]


def outcome_lines(card: dict) -> list[str]:
    if card["state"] == ANSWERED_STATE:
        answer = card["answer"]
        return [
            "",
            f"**Answer** ({answer['decided_by']}, {answer['decided_at']}): {answer['choice']}",
            f"Rationale: {answer['rationale']}",
        ]
    if card["state"] == WITHDRAWN_STATE:
        return ["", f"**Withdrawn**: {card['withdrawal']['reason']}"]
    return []


def rendered_card(card: dict) -> str:
    reversibility = "reversible" if card["reversible"] else "irreversible"
    lines = [
        f"## {card['id']} · {card['state']} · from {card['requester']} to {card['orchestrator']}",
        "",
        f"**Question**: {card['question']}",
    ]
    if card.get("goal"):
        lines.append(f"**Goal**: {card['goal']}")
    lines += [
        f"**Blocked work**: {card['blocked_work']}",
        f"**Blast radius** ({reversibility}): {card['blast_radius']}",
        "",
        "**Options**",
        *(option_line(option, card["recommendation"]) for option in card["options"]),
        "",
        f"**Recommendation**: {card['recommendation']}. {card['reasoning']}",
        "",
        "**Evidence**",
        *(f"- {item}" for item in card["evidence"]),
        *assumption_lines(card),
        *outcome_lines(card),
    ]
    return "\n".join(lines)


def summary_row(card: dict) -> str:
    return "\t".join(
        [
            card["id"],
            card["state"],
            card["requester"],
            card["orchestrator"],
            card["question"],
        ]
    )


def notification_text(card: dict) -> str:
    if card["state"] == ANSWERED_STATE:
        answer = card["answer"]
        return (
            f"decision {card['id']} answered by {answer['decided_by']}: {answer['choice']}. "
            f"Rationale: {answer['rationale']}. Full card: a2a decision show {card['id']}"
        )
    return f"decision {card['id']} for you from {card['requester']}: {card['question']} Read it: a2a decision show {card['id']}"
