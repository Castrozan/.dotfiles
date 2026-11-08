from __future__ import annotations

from .cards import ANSWERED_STATE, WITHDRAWN_STATE
from .delegation import human_only_grounds


def option_line(option: dict, recommendation: str) -> str:
    marker = " (recommended)" if option["label"] == recommendation else ""
    return f"- **{option['label']}**{marker}: {option['consequence']}"


def bulleted_section(title: str, items: list[str]) -> list[str]:
    if not items:
        return []
    return ["", f"**{title}**", *(f"- {item}" for item in items)]


def answer_lines(answer: dict) -> list[str]:
    return [
        "",
        f"**Answer** ({answer['decided_by']}, {answer['decided_at']}): "
        f"{answer['choice']}",
        f"Rationale: {answer['rationale']}",
    ]


def outcome_lines(card: dict) -> list[str]:
    if card["state"] == ANSWERED_STATE:
        return answer_lines(card["answer"])
    if card["state"] == WITHDRAWN_STATE:
        return ["", f"**Withdrawn**: {card['withdrawal']['reason']}"]
    return []


def decider_line(card: dict) -> str:
    grounds = human_only_grounds(card)
    if grounds:
        return f"**Decider**: the human only ({', '.join(grounds)})"
    return (
        "**Decider**: the orchestrator when a standing order covers it, else the human"
    )


def heading_lines(card: dict) -> list[str]:
    lines = [
        f"## {card['id']} · {card['state']} · from {card['requester']} "
        f"to {card['orchestrator']}",
        "",
        f"**Question**: {card['question']}",
    ]
    if card.get("goal"):
        lines.append(f"**Goal**: {card['goal']}")
    return lines


def rendered_card(card: dict) -> str:
    reversibility = "reversible" if card["reversible"] else "irreversible"
    lines = [
        *heading_lines(card),
        f"**Blocked work**: {card['blocked_work']}",
        f"**Blast radius** ({reversibility}): {card['blast_radius']}",
        decider_line(card),
        "",
        "**Options**",
        *(option_line(option, card["recommendation"]) for option in card["options"]),
        "",
        f"**Recommendation**: {card['recommendation']}. {card['reasoning']}",
        *bulleted_section("Evidence", card["evidence"]),
        *bulleted_section("Unverified assumptions", card["unverified_assumptions"]),
        *outcome_lines(card),
    ]
    return "\n".join(lines)


def summary_row(card: dict) -> str:
    decided_by = card["answer"]["decided_by"] if "answer" in card else "-"
    return "\t".join(
        [
            card["id"],
            card["state"],
            decided_by,
            card["requester"],
            card["orchestrator"],
            card["question"],
        ]
    )


def notification_text(card: dict) -> str:
    show_command = f"a2a decision show {card['id']}"
    if card["state"] == ANSWERED_STATE:
        answer = card["answer"]
        return (
            f"decision {card['id']} answered by {answer['decided_by']}: "
            f"{answer['choice']}. Rationale: {answer['rationale']}. "
            f"Full card: {show_command}"
        )
    if card["state"] == WITHDRAWN_STATE:
        return f"decision {card['id']} withdrawn by {card['requester']}: {show_command}"
    return (
        f"decision {card['id']} for you from {card['requester']}: "
        f"{card['question']} Read it: {show_command}"
    )
