#!/usr/bin/env python3

from __future__ import annotations

import re

SHORT_CONFIRMATION_MAXIMUM_PROSE_LINES = 3
SCANNABLE_MAXIMUM_PROSE_LINES = 14
REPLY_TARGET_PROSE_WORDS = 150
REPLY_HARD_WORD_CEILING = 250
REPLY_HARD_CHARACTER_CEILING = 1500
MAXIMUM_PROSE_PARAGRAPH_BLOCKS = 4

DONE_LABEL_PATTERN = re.compile(
    r"^\s*\*{0,2}done\*{0,2}\s*:", re.IGNORECASE | re.MULTILINE
)
NEXT_LABEL_PATTERN = re.compile(
    r"^\s*\*{0,2}next\*{0,2}\s*:", re.IGNORECASE | re.MULTILINE
)

LIST_MARKER_LINE_PATTERN = re.compile(r"^\s*([-*+]\s|\d+[.)]\s)")
MARKDOWN_HEADER_LINE_PATTERN = re.compile(r"^\s*#{1,6}\s")

LONG_FORM_PRODUCE_VERB = (
    r"(write|draft|compose|produce|generate|create|make|build|author|put together)"
)
LONG_FORM_ARTIFACT_NOUN = (
    r"(docs?|documentation|document|write-?up|essay|readme|runbook|guide|tutorial|"
    r"specification|proposal|diagram|deep[- ]?dive|walkthrough)"
)
LONG_FORM_ARTIFACT_REQUEST_PATTERN = re.compile(
    r"\b"
    + LONG_FORM_PRODUCE_VERB
    + r"\b[^.\n?!;]{0,60}?\b"
    + LONG_FORM_ARTIFACT_NOUN
    + r"\b",
    re.IGNORECASE,
)
LONG_FORM_DIRECTIVE_PATTERN = re.compile(
    r"\b(in (full|detail)|long[- ]form|verbatim|do\s*n.?t summari[sz]e|no summary|"
    r"full (picture|breakdown|architecture|overview|write-?up)|as much detail|"
    r"the (full|whole|entire) (file|code|script|function|contents|diff|output|log))\b",
    re.IGNORECASE,
)


def prose_lines_outside_code_fences(reply_text: str) -> list[str]:
    prose_lines: list[str] = []
    inside_code_fence = False
    for line in reply_text.splitlines():
        if line.lstrip().startswith("```"):
            inside_code_fence = not inside_code_fence
            continue
        if inside_code_fence:
            continue
        if line.strip():
            prose_lines.append(line)
    return prose_lines


def prose_paragraph_block_count(reply_text: str) -> int:
    blocks = 0
    inside_code_fence = False
    inside_block = False
    for line in reply_text.splitlines():
        if line.lstrip().startswith("```"):
            inside_code_fence = not inside_code_fence
            inside_block = False
            continue
        if inside_code_fence:
            continue
        if line.strip():
            if not inside_block:
                blocks += 1
                inside_block = True
        else:
            inside_block = False
    return blocks


def user_request_permits_long_form(user_request_text: str) -> bool:
    if not user_request_text:
        return False
    return bool(
        LONG_FORM_ARTIFACT_REQUEST_PATTERN.search(user_request_text)
        or LONG_FORM_DIRECTIVE_PATTERN.search(user_request_text)
    )


def shape_and_length_violations(reply_text: str) -> list[str]:
    violations: list[str] = []
    prose_lines = prose_lines_outside_code_fences(reply_text)
    prose_word_count = sum(len(line.split()) for line in prose_lines)
    prose_character_count = sum(len(line) for line in prose_lines)
    paragraph_block_count = prose_paragraph_block_count(reply_text)
    has_done_and_next_labels = bool(
        DONE_LABEL_PATTERN.search(reply_text) and NEXT_LABEL_PATTERN.search(reply_text)
    )

    if any(LIST_MARKER_LINE_PATTERN.match(line) for line in prose_lines):
        violations.append("uses a bullet or numbered list instead of prose")
    if any(MARKDOWN_HEADER_LINE_PATTERN.match(line) for line in prose_lines):
        violations.append("uses a section header")

    if (
        len(prose_lines) > SHORT_CONFIRMATION_MAXIMUM_PROSE_LINES
        and not has_done_and_next_labels
    ):
        violations.append(
            "longer than a confirmation but missing the **Done:**/**Next:** labels"
        )
    if len(prose_lines) > SCANNABLE_MAXIMUM_PROSE_LINES:
        violations.append(
            f"runs {len(prose_lines)} prose lines, past the "
            f"{SCANNABLE_MAXIMUM_PROSE_LINES}-line scannable cap"
        )
    if prose_word_count > REPLY_HARD_WORD_CEILING:
        violations.append(
            f"runs {prose_word_count} prose words, a wall past the "
            f"{REPLY_HARD_WORD_CEILING}-word hard ceiling"
        )
    if prose_character_count > REPLY_HARD_CHARACTER_CEILING:
        violations.append(
            f"runs {prose_character_count} prose characters, a wall past the "
            f"{REPLY_HARD_CHARACTER_CEILING}-character hard ceiling"
        )
    if paragraph_block_count > MAXIMUM_PROSE_PARAGRAPH_BLOCKS:
        violations.append(
            f"stacks {paragraph_block_count} prose paragraphs, past the "
            f"{MAXIMUM_PROSE_PARAGRAPH_BLOCKS}-block ceiling of opening, Done, Next, and an "
            "optional Assumed line"
        )

    return violations
