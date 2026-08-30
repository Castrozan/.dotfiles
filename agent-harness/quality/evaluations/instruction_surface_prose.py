from pathlib import Path

from ai_instruction_format import instruction_body_lines

MAXIMUM_INSTRUCTION_LINE_LENGTH = 120
EXEMPT_LINE_PREFIXES = ("#", "|", "<!--")


def lines_outside_fenced_blocks(text: str) -> list[tuple[int, str]]:
    lines = []
    fenced = False
    for number, line in instruction_body_lines(text):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            lines.append((number, line))
    return lines


def line_is_exempt_from_the_wrap(line: str) -> bool:
    stripped = line.lstrip()
    if stripped.startswith(EXEMPT_LINE_PREFIXES):
        return True
    words = stripped.split()
    return bool(words) and len(words[0]) > MAXIMUM_INSTRUCTION_LINE_LENGTH


def over_length_lines(path: Path) -> list[tuple[int, int]]:
    return [
        (number, len(line))
        for number, line in lines_outside_fenced_blocks(path.read_text())
        if len(line) > MAXIMUM_INSTRUCTION_LINE_LENGTH
        and not line_is_exempt_from_the_wrap(line)
    ]
