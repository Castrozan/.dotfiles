from __future__ import annotations

import textwrap

COLUMN_SEPARATOR = " │ "
ROW_SEPARATOR_JOINT = "─┼─"


def wrapped_cell(text: str, width: int) -> list[str]:
    return textwrap.wrap(text, width, break_on_hyphens=False) or [""]


def table_row_lines(cells: list[str], widths: list[int]) -> list[str]:
    columns = [
        wrapped_cell(cell, width) for cell, width in zip(cells, widths, strict=True)
    ]
    height = max(len(column) for column in columns)
    return [
        COLUMN_SEPARATOR.join(
            (column[index] if index < len(column) else "").ljust(width)
            for column, width in zip(columns, widths, strict=True)
        ).rstrip()
        for index in range(height)
    ]


def text_table(headers: list[str], rows: list[list[str]], widths: list[int]) -> str:
    separator = ROW_SEPARATOR_JOINT.join("─" * width for width in widths)
    lines = table_row_lines(headers, widths)
    for row in rows:
        lines += [separator, *table_row_lines(row, widths)]
    return "\n".join(lines)
