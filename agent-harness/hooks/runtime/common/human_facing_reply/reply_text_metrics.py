#!/usr/bin/env python3

from __future__ import annotations

import re

from reply_template_limits import REQUIRED_REPLY_LABELS

BOX_DRAWING_CHARACTERS = frozenset("─│┌┐└┘├┤┬┴┼╭╮╯╰━┃┏┓┗┛╔╗╚╝║═")
TABLE_ROW_PREFIX = "|"
CODE_FENCE_PREFIX = "```"
EMPHASIS_MARKER = "**"

LIST_MARKER_LINE_PATTERN = re.compile(r"^\s*([-*+]\s|\d+[.)]\s)")
BLOCK_QUOTE_LINE_PATTERN = re.compile(r"^\s*>")
INLINE_CODE_SPAN_PATTERN = re.compile(r"`[^`]*`")
QUOTED_SPAN_PATTERN = re.compile(r"[\"“][^\"”]*[\"”]")


def reply_label_pattern(label: str) -> re.Pattern[str]:
    return re.compile(rf"^\s*\*{{0,2}}{label}\*{{0,2}}\s*:", re.IGNORECASE)


REPLY_LABEL_PATTERNS = {
    label: reply_label_pattern(label) for label in REQUIRED_REPLY_LABELS
}


def is_visual_line(line: str) -> bool:
    if line.strip().startswith(TABLE_ROW_PREFIX):
        return True
    return any(character in BOX_DRAWING_CHARACTERS for character in line)


def prose_lines_outside_visuals(reply_text: str) -> list[str]:
    prose_lines: list[str] = []
    inside_code_fence = False
    for line in reply_text.splitlines():
        if line.lstrip().startswith(CODE_FENCE_PREFIX):
            inside_code_fence = not inside_code_fence
            continue
        if inside_code_fence or not line.strip() or is_visual_line(line):
            continue
        prose_lines.append(line)
    return prose_lines


def list_line_blocks(prose_lines: list[str]) -> list[list[str]]:
    blocks: list[list[str]] = []
    current_block: list[str] = []
    for line in prose_lines:
        if LIST_MARKER_LINE_PATTERN.match(line):
            current_block.append(line)
            continue
        if current_block:
            blocks.append(current_block)
            current_block = []
    if current_block:
        blocks.append(current_block)
    return blocks


def matched_reply_label(line: str) -> str | None:
    for label, pattern in REPLY_LABEL_PATTERNS.items():
        if pattern.match(line):
            return label
    return None


def line_starts_a_reply_label(line: str) -> bool:
    return matched_reply_label(line) is not None


class ReplyLabelLine:
    def __init__(self, label: str, text: str, preceded_by_blank_line: bool):
        self.label = label
        self.text = text
        self.preceded_by_blank_line = preceded_by_blank_line
        self.is_emphasized = text.strip().startswith(EMPHASIS_MARKER)


def reply_label_lines(reply_text: str) -> list[ReplyLabelLine]:
    label_lines: list[ReplyLabelLine] = []
    inside_code_fence = False
    previous_line_was_blank = True
    for line in reply_text.splitlines():
        if line.lstrip().startswith(CODE_FENCE_PREFIX):
            inside_code_fence = not inside_code_fence
            previous_line_was_blank = False
            continue
        if inside_code_fence:
            continue
        if not line.strip():
            previous_line_was_blank = True
            continue
        label = matched_reply_label(line)
        if label:
            label_lines.append(ReplyLabelLine(label, line, previous_line_was_blank))
        previous_line_was_blank = False
    return label_lines


def labels_present_in(prose_lines: list[str]) -> set[str]:
    return {
        label
        for label, pattern in REPLY_LABEL_PATTERNS.items()
        if any(pattern.match(line) for line in prose_lines)
    }


def labeled_section_word_count(prose_lines: list[str]) -> int:
    words = 0
    inside_labeled_section = False
    for line in prose_lines:
        if line_starts_a_reply_label(line):
            inside_labeled_section = True
        if inside_labeled_section:
            words += len(line.split())
    return words


def text_without_quotations(prose_text: str) -> str:
    unquoted_lines = [
        line
        for line in prose_text.splitlines()
        if not BLOCK_QUOTE_LINE_PATTERN.match(line)
    ]
    unquoted_text = "\n".join(unquoted_lines)
    unquoted_text = INLINE_CODE_SPAN_PATTERN.sub(" ", unquoted_text)
    return QUOTED_SPAN_PATTERN.sub(" ", unquoted_text)


class ReplyUnderReview:
    def __init__(self, reply_text: str):
        self.text = reply_text
        self.text_without_leading_space = reply_text.lstrip()
        self.prose_lines = prose_lines_outside_visuals(reply_text)
        self.prose_text = "\n".join(self.prose_lines)
        self.prose_without_quotations = text_without_quotations(self.prose_text)
        self.prose_word_count = sum(len(line.split()) for line in self.prose_lines)
        self.list_blocks = list_line_blocks(self.prose_lines)
        self.labels_present = labels_present_in(self.prose_lines)
        self.labeled_section_word_count = labeled_section_word_count(self.prose_lines)
        self.label_lines = reply_label_lines(reply_text)
