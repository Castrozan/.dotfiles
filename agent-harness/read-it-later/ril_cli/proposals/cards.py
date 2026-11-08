from __future__ import annotations

from collections import Counter

from proposals.card_example import EXAMPLE_CARDS_DOCUMENT
from pull_requests import TOPIC_SLUG_PATTERN

ACTIONS = ("drop", "file", "session")
SESSION_HOSTS = ("chise", "kira")
GROUP_FIELDS = {"topic_slug": str, "title": str, "bundle_goal": str, "cards": list}
CARD_FIELDS = {
    "capture": str,
    "tldr": str,
    "origin_url": str,
    "linked_urls": list,
    "covered_evidence": list,
    "second_brain_direction": list,
    "systems": list,
    "runs_locally_on_chise": bool,
    "lucas_note": str,
    "action": str,
    "reason": str,
}
ENTRY_FIELDS = {
    "title": str,
    "theme_moc": str,
    "tags": list,
    "why": str,
    "what_to_steal": list,
    "reuse_for": str,
    "creator": str,
    "platform": str,
}
SESSION_FIELDS = {"host": str, "done_when": list, "constraints": list}


class CardsInvalid(ValueError):
    def __init__(self, problems: list[str]) -> None:
        super().__init__("\n".join(problems))
        self.problems = problems


def field_problems(document, fields: dict, location: str) -> list[str]:
    if not isinstance(document, dict):
        return [f"{location} must be an object"]
    return [
        f"{location}.{name} must be {expected_type.__name__}"
        for name, expected_type in fields.items()
        if not isinstance(document.get(name), expected_type)
    ]


def target_problems(group: dict, location: str) -> list[str]:
    target = group.get("target_pull_request")
    if target is None or (isinstance(target, int) and not isinstance(target, bool)):
        return []
    return [f"{location}.target_pull_request must be a pull request number or null"]


def card_problems(card: dict, location: str) -> list[str]:
    problems = field_problems(card, CARD_FIELDS, location)
    if problems:
        return problems
    if card["action"] not in ACTIONS:
        return [f"{location}.action must be one of {', '.join(ACTIONS)}"]
    if card["action"] == "file":
        return field_problems(card.get("entry"), ENTRY_FIELDS, f"{location}.entry")
    return []


def session_problems(group: dict, location: str) -> list[str]:
    if not any(card.get("action") == "session" for card in group["cards"]):
        return []
    session = group.get("session")
    problems = field_problems(session, SESSION_FIELDS, f"{location}.session")
    if not problems and session["host"] not in SESSION_HOSTS:
        problems.append(
            f"{location}.session.host must be one of {', '.join(SESSION_HOSTS)}"
        )
    return problems


def group_problems(group: dict, location: str) -> list[str]:
    problems = field_problems(group, GROUP_FIELDS, location)
    if problems:
        return problems
    if not TOPIC_SLUG_PATTERN.match(group["topic_slug"]):
        problems.append(
            f"{location}.topic_slug must be lowercase words joined by hyphens"
        )
    if not group["cards"]:
        problems.append(f"{location}.cards must not be empty")
    problems += target_problems(group, location)
    for position, card in enumerate(group["cards"]):
        problems += card_problems(card, f"{location}.cards[{position}]")
    return problems + session_problems(group, location)


def duplicate_capture_problems(groups: list[dict]) -> list[str]:
    counted = Counter(
        card.get("capture")
        for group in groups
        for card in group.get("cards", [])
        if isinstance(card, dict)
    )
    return [
        f"capture {name} appears in more than one card"
        for name, count in counted.items()
        if count > 1
    ]


def validated_cards_document(document) -> list[dict]:
    groups = document.get("groups") if isinstance(document, dict) else None
    if not isinstance(groups, list) or not groups:
        raise CardsInvalid(["the cards document needs a non-empty groups list"])
    problems = [
        problem
        for position, group in enumerate(groups)
        for problem in group_problems(group, f"groups[{position}]")
    ]
    problems += duplicate_capture_problems(groups)
    if problems:
        raise CardsInvalid(problems)
    return groups


def example_cards_document() -> dict:
    return EXAMPLE_CARDS_DOCUMENT
