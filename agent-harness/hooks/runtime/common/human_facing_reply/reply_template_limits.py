#!/usr/bin/env python3

from __future__ import annotations

SHORT_CONFIRMATION_MAXIMUM_PROSE_WORDS = 100
UNLABELED_BODY_WORD_CEILING = 80
LABELED_SECTION_WORD_CEILING = 50
MAXIMUM_LIST_BLOCK_LINES = 5
MAXIMUM_LIST_LINE_WORDS = 20
REQUIRED_REPLY_LABELS = ("What is this session about?", "done", "next")
PER_LABEL_WORD_CEILINGS = {
    "What is this session about?": 25,
    "done": 20,
    "next": 20,
}
