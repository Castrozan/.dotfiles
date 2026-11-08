from __future__ import annotations

import textwrap

from .delegation import human_only_grounds

CARD_WIDTH = 100


def sentence(text: str) -> str:
    text = text.strip()
    return text if text.endswith((".", "?", "!")) else f"{text}."


def options_sentence(card: dict) -> str:
    described = "; ".join(
        f"{option['label']}, which means {option['consequence'].rstrip('.')}"
        for option in card["options"]
    )
    return f"The options are {described}."


def evidence_sentences(card: dict) -> list[str]:
    sentences = [f"Evidence: {'; '.join(card['evidence'])}."]
    if card["unverified_assumptions"]:
        unverified = "; ".join(card["unverified_assumptions"])
        sentences.append(f"Not verified: {unverified}.")
    return sentences


def details_sentences(card: dict) -> list[str]:
    return [f"Full detail: {card['details']}."] if "details" in card else []


def authority_sentence(card: dict) -> str:
    grounds = human_only_grounds(card)
    reversibility = "It is reversible" if card["reversible"] else "It is irreversible"
    reserved = f" and reserved to you ({', '.join(grounds)})" if grounds else ""
    blast_radius = card["blast_radius"].rstrip(".")
    return f"{reversibility}{reserved}; blast radius: {blast_radius}."


def escalation_sentence(escalation: dict) -> str:
    return (
        f"The orchestrator escalated it ({escalation['reason']}): "
        f"{sentence(escalation['missing'])}"
    )


def answer_sentence(answer: dict) -> str:
    cited = f" under {answer['directive']}" if "directive" in answer else ""
    return (
        f"Decided by {answer['decided_by']}{cited}: {answer['choice']}, "
        f"because {sentence(answer['rationale'])}"
    )


def override_sentence(override: dict) -> str:
    return f"Overridden by you: {override['choice']}, {sentence(override['rationale'])}"


def outcome_sentences(card: dict) -> list[str]:
    renderers = (
        ("escalation", escalation_sentence),
        ("answer", answer_sentence),
        ("override", override_sentence),
    )
    return [render(card[field]) for field, render in renderers if field in card]


def decision_paragraph(card: dict) -> str:
    sentences = [
        f"{card['requester']} needs a decision: {sentence(card['question'])}",
        f"It blocks {sentence(card['blocked_work'])}",
        options_sentence(card),
        f"It recommends {card['recommendation']} because {sentence(card['reasoning'])}",
        *evidence_sentences(card),
        *details_sentences(card),
        authority_sentence(card),
        *outcome_sentences(card),
    ]
    return " ".join(sentences)


def wrapped_block(text: str) -> str:
    return textwrap.fill(text, CARD_WIDTH, break_on_hyphens=False)


def rendered_card(card: dict) -> str:
    blocks = [
        f"{card['id']} ({card['state']})",
        decision_paragraph(card),
        f"**What is this session about?:** {sentence(card['goal'])}",
        f"**Done:** {sentence(card['progress'])}",
        f"**Next:** {sentence(card['blocked_work'])}",
    ]
    return "\n\n".join(map(wrapped_block, blocks))


def summary_row(card: dict) -> str:
    decided_by = card.get("answer", {}).get("decided_by", "-")
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
    show_command = f"orchestrator decision show {card['id']}"
    if card["state"] == "overridden":
        return (
            f"decision {card['id']} overridden by the human: "
            f"{card['override']['choice']}. Rework to match it: {show_command}"
        )
    if card["state"] == "answered":
        answer = card["answer"]
        return (
            f"decision {card['id']} answered by {answer['decided_by']}: "
            f"{answer['choice']}. Rationale: {answer['rationale']}. "
            f"Full card: {show_command}"
        )
    if card["state"] == "withdrawn":
        return f"decision {card['id']} withdrawn by {card['requester']}: {show_command}"
    return (
        f"decision {card['id']} for you from {card['requester']}: "
        f"{card['question']} Read it: {show_command}"
    )
