from __future__ import annotations

import textwrap
from datetime import datetime

from .text_table import text_table

ROUND_WIDTH = 100
OPTION_WIDTHS = [2, 28, 64]
SESSION_WIDTHS = [2, 14, 22, 26, 21]
SESSION_HEADERS = ["#", "Session", "About", "This round", "Blocks"]


def paragraph(text: str) -> str:
    return textwrap.fill(text, ROUND_WIDTH, break_on_hyphens=False)


def option_rows(card: dict) -> list[list[str]]:
    return [
        [
            str(index),
            option["label"]
            + (" (recommended)" if option["label"] == card["recommendation"] else ""),
            option["consequence"],
        ]
        for index, option in enumerate(card["options"], start=1)
    ]


def card_facts(card: dict) -> str:
    reversibility = "reversible" if card["reversible"] else "irreversible"
    facts = [f"Blocks: {card['blocked_work']}", reversibility]
    if "details" in card:
        facts.append(f"detail: {card['details']}")
    return " · ".join(facts)


def decision_block(card: dict) -> str:
    return "\n".join(
        [
            paragraph(f"{card['id']} · {card['requester']}, working to {card['goal']}"),
            paragraph(f"Asks: {card['question']}"),
            text_table(
                ["#", "Option", "What happens"], option_rows(card), OPTION_WIDTHS
            ),
            paragraph(f"Recommended because: {card['reasoning']}"),
            paragraph(card_facts(card)),
        ]
    )


def minutes_since(timestamp: str, now: datetime) -> int:
    return int((now - datetime.fromisoformat(timestamp)).total_seconds() // 60)


def blocks_cell(report: dict) -> str:
    decisions = report["open_decisions"]
    waiting = f" Waiting on {', '.join(decisions)}." if decisions else ""
    return f"{report['next_step']}{waiting}"


def session_rows(reports: list[dict], now: datetime) -> list[list[str]]:
    return [
        [
            str(index),
            f"{report['requester']} {report['state']}, "
            f"{minutes_since(report['updated_at'], now)} min ago",
            report["goal"],
            report["progress"],
            blocks_cell(report),
        ]
        for index, report in enumerate(reports, start=1)
    ]


def rendered_round(cards: list[dict], reports: list[dict], now: datetime) -> str:
    decisions = [decision_block(card) for card in cards] or [
        "No decision is waiting for you."
    ]
    sessions = (
        text_table(SESSION_HEADERS, session_rows(reports, now), SESSION_WIDTHS)
        if reports
        else "No session has filed a report."
    )
    return "\n\n".join(["Decisions waiting for you", *decisions, "Sessions", sessions])
