from __future__ import annotations

import json
import re

CARD_DATA_MARKER = "<!-- ril-cards -->"
CARD_DATA_BLOCK = re.compile(
    re.escape(CARD_DATA_MARKER) + r"\s*```json\n(?P<data>.*?)\n```", re.DOTALL
)
TABLE_HEADER = "| # | Capture | TL;DR | Action | Why | Already covered | Second Brain direction | Systems | Local | Lucas's note |"
TABLE_RULE = "|---|---|---|---|---|---|---|---|---|---|"
ANSWER_GUIDE = (
    "Answer on the pull request in plain language: approve the table as it stands, change any card "
    '("drop 3", "session for 2 on kira"), or ask. Captures added after your approval need a new one.'
)


class DecisionFileUnreadable(ValueError):
    pass


def table_cell(value) -> str:
    text = "; ".join(map(str, value)) if isinstance(value, list) else str(value)
    return text.replace("|", "\\|").replace("\n", " ").strip() or "-"


def action_cell(card: dict) -> str:
    if card["action"] == "file":
        return f"file → {card['entry']['title']} ({card['entry']['theme_moc']})"
    return card["action"]


def card_row(position: int, card: dict) -> str:
    cells = [
        str(position),
        f"[{table_cell(card['capture'].removesuffix('.md'))}]({card['origin_url']})",
        table_cell(card["tldr"]),
        table_cell(action_cell(card)),
        table_cell(card["reason"]),
        table_cell(card["covered_evidence"]),
        table_cell(card["second_brain_direction"]),
        table_cell(card["systems"]),
        "yes" if card["runs_locally_on_chise"] else "no",
        table_cell(card["lucas_note"]),
    ]
    return f"| {' | '.join(cells)} |"


def cards_table(group: dict) -> str:
    rows = [card_row(position, card) for position, card in enumerate(group["cards"], 1)]
    return "\n".join([TABLE_HEADER, TABLE_RULE, *rows])


def session_section(group: dict) -> str:
    session = group.get("session")
    if not session:
        return ""
    done_when = "\n".join(f"- {item}" for item in session["done_when"])
    constraints = "\n".join(f"- {item}" for item in session["constraints"])
    return f"\n## Session on {session['host']}\n\nDone when:\n{done_when}\n\nConstraints:\n{constraints}\n"


def render_summary(group: dict) -> str:
    return f"**Bundle goal:** {group['bundle_goal']}\n\n{cards_table(group)}\n{session_section(group)}\n{ANSWER_GUIDE}\n"


def render_decision_file(group: dict) -> str:
    card_data = json.dumps(group, indent=2, ensure_ascii=False)
    return (
        f"# {group['title']}\n\n{render_summary(group)}\n<details><summary>Card data</summary>\n\n"
        f"{CARD_DATA_MARKER}\n```json\n{card_data}\n```\n\n</details>\n"
    )


def parse_decision_file(text: str) -> dict:
    matched_block = CARD_DATA_BLOCK.search(text)
    if matched_block is None:
        raise DecisionFileUnreadable("the decision file carries no card data block")
    try:
        return json.loads(matched_block.group("data"))
    except json.JSONDecodeError as error:
        raise DecisionFileUnreadable(
            f"the card data block is not JSON: {error}"
        ) from error
