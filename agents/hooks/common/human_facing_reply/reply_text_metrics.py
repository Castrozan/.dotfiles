#!/usr/bin/env python3

from __future__ import annotations

import re

DONE_LABEL_PATTERN = re.compile(
    r"^\s*\*{0,2}done\*{0,2}\s*:", re.IGNORECASE | re.MULTILINE
)
NEXT_LABEL_PATTERN = re.compile(
    r"^\s*\*{0,2}next\*{0,2}\s*:", re.IGNORECASE | re.MULTILINE
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


class ReplyUnderReview:
    def __init__(self, reply_text: str):
        self.text = reply_text
        self.text_without_leading_space = reply_text.lstrip()
        self.prose_lines = prose_lines_outside_code_fences(reply_text)
        self.prose_text = "\n".join(self.prose_lines)
        self.prose_line_count = len(self.prose_lines)
        self.prose_word_count = sum(len(line.split()) for line in self.prose_lines)
        self.prose_character_count = sum(len(line) for line in self.prose_lines)
        self.paragraph_block_count = prose_paragraph_block_count(reply_text)
        self.has_done_and_next_labels = bool(
            DONE_LABEL_PATTERN.search(reply_text)
            and NEXT_LABEL_PATTERN.search(reply_text)
        )
