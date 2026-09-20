#!/usr/bin/env python3

from __future__ import annotations

import re

from reply_text_metrics import (
    BLOCK_QUOTE_LINE_PATTERN,
    CODE_FENCE_PREFIX,
    INLINE_CODE_SPAN_PATTERN,
    QUOTED_SPAN_PATTERN,
    is_visual_line,
    matched_reply_label,
)

HORIZONTAL_SPACE = "[ \t]"
NUMERIC_RANGE_EN_DASH_PATTERN = re.compile(
    rf"(?<=\d){HORIZONTAL_SPACE}*–{HORIZONTAL_SPACE}*(?=\d)"
)
SENTENCE_DASH_PATTERN = re.compile(rf"{HORIZONTAL_SPACE}*[—–]{HORIZONTAL_SPACE}*")
REDUNDANT_PUNCTUATION_PATTERN = re.compile(rf",{HORIZONTAL_SPACE}*(?=[,;:.!?])")
PROTECTED_SPAN_PATTERN = re.compile(
    INLINE_CODE_SPAN_PATTERN.pattern + "|" + QUOTED_SPAN_PATTERN.pattern
)
LABEL_LINE_PATTERN = re.compile(
    rf"^({HORIZONTAL_SPACE}*)\*{{0,2}}([^*:]+)\*{{0,2}}:\*{{0,2}}{HORIZONTAL_SPACE}*(.*)$"
)
DANGLING_COMMA_LINE_START_PATTERN = re.compile(
    rf"^({HORIZONTAL_SPACE}*)(?:([-*+]){HORIZONTAL_SPACE}*)?,{HORIZONTAL_SPACE}*"
)
DANGLING_COMMA_LINE_END_PATTERN = re.compile(rf",{HORIZONTAL_SPACE}*$")
LINE_LEADING_DASH_PATTERN = re.compile(
    rf"^{HORIZONTAL_SPACE}*(?:[-*+]{HORIZONTAL_SPACE}+)?[—–]"
)
LINE_TRAILING_DASH_PATTERN = re.compile(rf"[—–]{HORIZONTAL_SPACE}*$")


def dashes_replaced_outside_protected_spans(line: str) -> str:
    repaired_segments: list[str] = []
    cursor = 0
    for protected_span in PROTECTED_SPAN_PATTERN.finditer(line):
        repaired_segments.append(
            dashes_replaced_in_plain_text(line[cursor : protected_span.start()])
        )
        repaired_segments.append(protected_span.group(0))
        cursor = protected_span.end()
    repaired_segments.append(dashes_replaced_in_plain_text(line[cursor:]))
    return "".join(repaired_segments)


def dashes_replaced_in_plain_text(text: str) -> str:
    without_numeric_ranges = NUMERIC_RANGE_EN_DASH_PATTERN.sub("-", text)
    without_sentence_dashes = SENTENCE_DASH_PATTERN.sub(", ", without_numeric_ranges)
    return REDUNDANT_PUNCTUATION_PATTERN.sub("", without_sentence_dashes)


def line_start_without_comma(start_match: re.Match[str]) -> str:
    indentation, list_marker = start_match.groups()
    return indentation + (f"{list_marker} " if list_marker else "")


def dangling_commas_trimmed(original_line: str, repaired_line: str) -> str:
    if LINE_LEADING_DASH_PATTERN.match(original_line):
        repaired_line = DANGLING_COMMA_LINE_START_PATTERN.sub(
            line_start_without_comma, repaired_line
        )
    if LINE_TRAILING_DASH_PATTERN.search(original_line):
        repaired_line = DANGLING_COMMA_LINE_END_PATTERN.sub("", repaired_line)
    return repaired_line


def label_line_with_emphasis(line: str) -> str:
    label_match = LABEL_LINE_PATTERN.match(line)
    if not label_match:
        return line
    indentation, label_text, remainder = label_match.groups()
    emphasized_label = f"{indentation}**{label_text.strip()}:**"
    return f"{emphasized_label} {remainder}".rstrip()


def repaired_prose_line(line: str) -> str:
    repaired_line = line
    if not is_visual_line(line) and not BLOCK_QUOTE_LINE_PATTERN.match(line):
        repaired_line = dangling_commas_trimmed(
            line, dashes_replaced_outside_protected_spans(line)
        )
    if matched_reply_label(repaired_line):
        repaired_line = label_line_with_emphasis(repaired_line)
    return repaired_line


def repaired_reply_text(reply_text: str) -> str:
    repaired_lines: list[str] = []
    inside_code_fence = False
    previous_line_was_blank = True
    for line in reply_text.splitlines():
        line_opens_or_closes_a_fence = line.lstrip().startswith(CODE_FENCE_PREFIX)
        if line_opens_or_closes_a_fence:
            inside_code_fence = not inside_code_fence
        if inside_code_fence or line_opens_or_closes_a_fence or not line.strip():
            repaired_lines.append(line)
            previous_line_was_blank = not line.strip()
            continue
        repaired_line = repaired_prose_line(line)
        if matched_reply_label(repaired_line) and not previous_line_was_blank:
            repaired_lines.append("")
        repaired_lines.append(repaired_line)
        previous_line_was_blank = False
    repaired_text = "\n".join(repaired_lines)
    if reply_text.endswith("\n"):
        repaired_text += "\n"
    return repaired_text
