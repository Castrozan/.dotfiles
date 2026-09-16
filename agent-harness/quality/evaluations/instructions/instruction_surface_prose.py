from pathlib import Path

from instructions.instruction_markdown_frontmatter import parse_instruction_body

MAXIMUM_INSTRUCTION_LINE_LENGTH = 120
EXEMPT_LINE_PREFIXES = ("### ",)


def line_is_exempt_from_the_wrap(line: str) -> bool:
    stripped = line.lstrip()
    if stripped.startswith(EXEMPT_LINE_PREFIXES):
        return True
    words = stripped.split()
    return bool(words) and len(words[0]) > MAXIMUM_INSTRUCTION_LINE_LENGTH


def over_length_lines(path: Path) -> list[tuple[int, int]]:
    body = parse_instruction_body(path.read_text())
    return [
        (number, len(line))
        for number, line in enumerate(body.text.splitlines(), body.first_line_number)
        if len(line) > MAXIMUM_INSTRUCTION_LINE_LENGTH
        and not line_is_exempt_from_the_wrap(line)
    ]
