from __future__ import annotations

CELL_CHARACTERS = 160
ELLIPSIS = "…"


def clipped(text: str, limit: int) -> str:
    flat = " ".join(text.split())
    if len(flat) <= limit:
        return flat
    return flat[: limit - len(ELLIPSIS)].rsplit(" ", 1)[0] + ELLIPSIS


def table_cell(text: str) -> str:
    return clipped(text, CELL_CHARACTERS).replace("|", "\\|")


def table_row(cells: list[str]) -> str:
    return "| " + " | ".join(table_cell(cell) for cell in cells) + " |"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    divider = "|" + "|".join("---" for _ in headers) + "|"
    return "\n".join([table_row(headers), divider, *map(table_row, rows)])
