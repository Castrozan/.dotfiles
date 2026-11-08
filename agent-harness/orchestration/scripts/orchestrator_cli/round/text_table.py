from __future__ import annotations

import textwrap

COLUMN_SEPARATOR = " │ "
ROW_SEPARATOR_JOINT = "─┼─"
ELLIPSIS = "…"


def clipped_lines(text: str, width: int, maximum_lines: int) -> list[str]:
    lines = textwrap.wrap(text, width, break_on_hyphens=False) or [""]
    if len(lines) <= maximum_lines:
        return lines
    kept = lines[:maximum_lines]
    kept[-1] = kept[-1][: width - len(ELLIPSIS)].rstrip() + ELLIPSIS
    return kept


def table_row_lines(
    cells: list[str], widths: list[int], maximum_lines: int
) -> list[str]:
    columns = [
        clipped_lines(cell, width, maximum_lines)
        for cell, width in zip(cells, widths, strict=True)
    ]
    height = max(len(column) for column in columns)
    return [
        COLUMN_SEPARATOR.join(
            (column[index] if index < len(column) else "").ljust(width)
            for column, width in zip(columns, widths, strict=True)
        ).rstrip()
        for index in range(height)
    ]


def text_table(
    headers: list[str], rows: list[list[str]], widths: list[int], maximum_lines: int
) -> str:
    separator = ROW_SEPARATOR_JOINT.join("─" * width for width in widths)
    lines = [*table_row_lines(headers, widths, 1), separator]
    for row in rows:
        lines += table_row_lines(row, widths, maximum_lines)
    return "\n".join(lines)
