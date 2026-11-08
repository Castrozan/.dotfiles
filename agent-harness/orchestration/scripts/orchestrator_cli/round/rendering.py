from __future__ import annotations

from datetime import datetime

from .text_table import clipped_lines, text_table

ROUND_WIDTH = 100
CELL_LINES = 2
OPTION_WIDTHS = [2, 30, 62]
SESSION_WIDTHS = [2, 20, 20, 26, 20]
SESSION_HEADERS = ["#", "Session", "About", "This round", "Blocks"]


def paragraph(text: str) -> str:
    return "\n".join(clipped_lines(text, ROUND_WIDTH, CELL_LINES))


def option_rows(card: dict) -> list[list[str]]:
    return [
        [str(index), option["label"], option["consequence"]]
        for index, option in enumerate(card["options"], start=1)
    ]


def blocking_line(card: dict) -> str:
    reversibility = "Reversible" if card["reversible"] else "Irreversible"
    return f"{reversibility}. Blocks {card['blocked_work']}"


def reply_line(card: dict) -> str:
    labels = ", ".join(option["label"] for option in card["options"])
    return f"Reply with {card['id']} and one option: {labels}"


def decision_block(card: dict) -> str:
    return "\n".join(
        [
            paragraph(f"{card['id']} · {card['requester']}, working to {card['goal']}"),
            paragraph(f"Asks: {card['question']}"),
            text_table(
                ["#", "Option", "What happens"],
                option_rows(card),
                OPTION_WIDTHS,
                CELL_LINES,
            ),
            paragraph(
                f"Recommends {card['recommendation']} because {card['reasoning']}"
            ),
            paragraph(blocking_line(card)),
            paragraph(reply_line(card)),
        ]
    )


def minutes_since(timestamp: str, now: datetime) -> int:
    return int((now - datetime.fromisoformat(timestamp)).total_seconds() // 60)


def blocks_cell(report: dict, now: datetime) -> str:
    decisions = report["open_decisions"]
    waiting = f" Waiting on {', '.join(decisions)}." if decisions else ""
    age = minutes_since(report["updated_at"], now)
    return f"{report['state']} {age}m: {report['next_step']}{waiting}"


def session_rows(reports: list[dict], now: datetime) -> list[list[str]]:
    return [
        [
            str(index),
            report["name"],
            report["goal"],
            report["progress"],
            blocks_cell(report, now),
        ]
        for index, report in enumerate(reports, start=1)
    ]


def rendered_round(cards: list[dict], reports: list[dict], now: datetime) -> str:
    decisions = [decision_block(card) for card in cards] or [
        "No decision is waiting for you."
    ]
    sessions = (
        text_table(
            SESSION_HEADERS, session_rows(reports, now), SESSION_WIDTHS, CELL_LINES
        )
        + "\nFull report: orchestrator report show <session>"
        if reports
        else "No session has filed a report."
    )
    return "\n\n".join(
        [
            "Decisions waiting for you\n" + "\n\n".join(decisions),
            "Sessions\n" + sessions,
        ]
    )
