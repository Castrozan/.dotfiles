#!/usr/bin/env python3

from __future__ import annotations


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


class ReplyUnderReview:
    def __init__(self, reply_text: str):
        self.prose_lines = prose_lines_outside_code_fences(reply_text)
        self.prose_text = "\n".join(self.prose_lines)
