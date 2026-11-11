from __future__ import annotations

import re
from datetime import datetime

from ..ledger.entries import ORCHESTRATOR_OWNER
from .markdown_table import ELLIPSIS, clipped, markdown_table

PARAGRAPH_CHARACTERS = 300
SESSION_HEADERS = ["#", "Session", "State", "Next"]
ASK_HEADERS = ["#", "You asked", "Handled by", "Asked"]
NEXT_CHARACTERS = 60
ASK_CHARACTERS = 70
ASK_ROWS = 5
LINK = re.compile(r"https?://\S+")
LINK_CHARACTERS = 40


def sentence(text: str) -> str:
    return text.strip().rstrip(".")


def paragraph(text: str) -> str:
    return clipped(text, PARAGRAPH_CHARACTERS)


def option_rows(card: dict) -> list[list[str]]:
    return [
        [str(index), option["label"], option["consequence"]]
        for index, option in enumerate(card["options"], start=1)
    ]


def recommendation_line(card: dict) -> str:
    reversibility = "Reversible" if card["reversible"] else "Irreversible"
    return (
        f"Recommends **{card['recommendation']}** because {sentence(card['reasoning'])}. "
        f"{reversibility}; blocks {card['blocked_work']}"
    )


def reply_line(card: dict) -> str:
    labels = ", ".join(option["label"] for option in card["options"])
    return f"Reply with `{card['id']}` and one option: {labels}"


def decision_block(card: dict) -> str:
    return "\n\n".join(
        [
            paragraph(
                f"**{card['id']} · {card['requester']}**, working to {sentence(card['goal'])}. "
                f"Asks: {card['question']}"
            ),
            markdown_table(["#", "Option", "What happens"], option_rows(card)),
            paragraph(recommendation_line(card)),
            paragraph(reply_line(card)),
        ]
    )


def minutes_since(timestamp: str, now: datetime) -> int:
    return int((now - datetime.fromisoformat(timestamp)).total_seconds() // 60)


def next_cell(report: dict) -> str:
    decisions = report["open_decisions"]
    if decisions:
        return f"waiting on {', '.join(decisions)}"
    return clipped(sentence(report["next_step"]), NEXT_CHARACTERS)


def session_rows(reports: list[dict], now: datetime) -> list[list[str]]:
    return [
        [
            str(index),
            report["name"],
            f"{report['state']} {minutes_since(report['updated_at'], now)}m",
            next_cell(report),
        ]
        for index, report in enumerate(reports, start=1)
    ]


def sessions_block(reports: list[dict], now: datetime) -> str:
    if not reports:
        return "No session has filed a report."
    return markdown_table(SESSION_HEADERS, session_rows(reports, now))


def age(timestamp: str, now: datetime) -> str:
    minutes = minutes_since(timestamp, now)
    if minutes < 120:
        return f"{minutes}m"
    hours = minutes // 60
    return f"{hours}h" if hours < 48 else f"{hours // 24}d"


def link_tail(link: str) -> str:
    if len(link) <= LINK_CHARACTERS:
        return link
    ending = link[-LINK_CHARACTERS:]
    _, slash, tail = ending.partition("/")
    return ELLIPSIS + (slash + tail if tail else ending)


def with_short_links(words: str) -> str:
    return LINK.sub(lambda link: link_tail(link.group()), words)


def handled_by(ask: dict, orchestrator: str) -> str:
    return orchestrator if ask["owner"] == ORCHESTRATOR_OWNER else ask["owner"]


def ask_rows(asks: list[dict], now: datetime, orchestrator: str) -> list[list[str]]:
    return [
        [
            str(index),
            clipped(with_short_links(ask["words"]), ASK_CHARACTERS),
            handled_by(ask, orchestrator),
            f"{age(ask['recorded_at'], now)} ago",
        ]
        for index, ask in enumerate(asks[:ASK_ROWS], start=1)
    ]


def asks_caption(orchestrator: str) -> str:
    return (
        f"Each row is something you asked {orchestrator} for, in your words. "
        f"It leaves once {orchestrator} has checked the real result, "
        "not only a session's report."
    )


def hidden_asks_line(hidden: int, orchestrator: str) -> str:
    return f"Newer requests not shown: {hidden}. Ask {orchestrator} for the full list."


def asks_block(asks: list[dict], now: datetime, orchestrator: str) -> list[str]:
    if not asks:
        return []
    table = markdown_table(ASK_HEADERS, ask_rows(asks, now, orchestrator))
    hidden = len(asks) - ASK_ROWS
    more = [hidden_asks_line(hidden, orchestrator)] if hidden > 0 else []
    return [
        "### Your requests not yet verified done",
        asks_caption(orchestrator),
        table,
        *more,
    ]


def rendered_round(
    cards: list[dict],
    reports: list[dict],
    asks: list[dict],
    now: datetime,
    orchestrator: str,
) -> str:
    decisions = [decision_block(card) for card in cards] or [
        "No decision is waiting for you."
    ]
    return "\n\n".join(
        [
            "### Sessions",
            sessions_block(reports, now),
            *asks_block(asks, now, orchestrator),
            "### Decisions waiting for you",
            *decisions,
        ]
    )
