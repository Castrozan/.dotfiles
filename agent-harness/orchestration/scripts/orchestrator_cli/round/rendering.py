from __future__ import annotations

from datetime import datetime

from .markdown_table import clipped, markdown_table

PARAGRAPH_CHARACTERS = 300
SESSION_HEADERS = ["#", "Session", "State", "Next"]
NEXT_CHARACTERS = 60
FULL_VIEW_LINE = (
    "Full view: `orchestrator decision show <id>` · "
    "`orchestrator report show <session>`"
)


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
    table = markdown_table(SESSION_HEADERS, session_rows(reports, now))
    return f"{table}\n\n{FULL_VIEW_LINE}"


def rendered_round(cards: list[dict], reports: list[dict], now: datetime) -> str:
    decisions = [decision_block(card) for card in cards] or [
        "No decision is waiting for you."
    ]
    return "\n\n".join(
        [
            "### Decisions waiting for you",
            *decisions,
            "### Sessions",
            sessions_block(reports, now),
        ]
    )
