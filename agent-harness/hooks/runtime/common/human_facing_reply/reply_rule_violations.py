#!/usr/bin/env python3

from __future__ import annotations

import re

from reply_template_limits import (
    LABELED_SECTION_WORD_CEILING,
    MAXIMUM_LIST_BLOCK_LINES,
    MAXIMUM_LIST_LINE_WORDS,
    REPLY_HARD_WORD_CEILING,
    REQUIRED_REPLY_LABELS,
    SHORT_CONFIRMATION_MAXIMUM_PROSE_WORDS,
)
from reply_text_metrics import ReplyUnderReview

EM_DASH_CHARACTER = "—"
EN_DASH_CHARACTER = "–"

SYCOPHANCY_OR_REACTION_OPENER_PATTERN = re.compile(
    r"^\s*(you're right|you are right|you're absolutely right|you are absolutely right|"
    r"good catch|great question|great point|i apologize|my apologies|sorry|absolutely|"
    r"sure thing|sure|of course|happy to)\b",
    re.IGNORECASE,
)

MECHANICS_NARRATION_OPENER_PATTERN = re.compile(
    r"^\s*(let me\b|let's\b|i'll go ahead|i'll now|now i'll|now let me|first,? i\b|"
    r"i'm going to|i am going to|i will now|i'm about to)",
    re.IGNORECASE,
)

TRACKABLE_ARTIFACT_REFERENCE_PATTERN = re.compile(
    r"\b(?:the|this|that)\s+(?:merge request|pull request)\b"
    r"|\bmerge request\s*!?\d+\b|\bpull request\s*#?\d+\b"
    r"|\bMR\s*!?\d+\b|\bPR\s*#?\d+\b",
    re.IGNORECASE,
)
URL_PRESENT_PATTERN = re.compile(r"https?://", re.IGNORECASE)


def sentence_dash_violation(reply: ReplyUnderReview) -> str | None:
    if EM_DASH_CHARACTER in reply.prose_without_quotations:
        return "contains an em dash outside a quotation"
    if EN_DASH_CHARACTER in reply.prose_without_quotations:
        return "contains an en dash outside a quotation"
    return None


def reaction_opener_violation(reply: ReplyUnderReview) -> str | None:
    if SYCOPHANCY_OR_REACTION_OPENER_PATTERN.match(reply.text_without_leading_space):
        return "opens with a reaction or sycophancy phrase"
    return None


def narration_opener_violation(reply: ReplyUnderReview) -> str | None:
    if MECHANICS_NARRATION_OPENER_PATTERN.match(reply.text_without_leading_space):
        return "opens by narrating what you are about to do"
    return None


def unlinked_artifact_violation(reply: ReplyUnderReview) -> str | None:
    names_artifact = TRACKABLE_ARTIFACT_REFERENCE_PATTERN.search(reply.prose_text)
    if names_artifact and not URL_PRESENT_PATTERN.search(reply.prose_text):
        return "names an MR or PR but gives no link to validate it"
    return None


def missing_required_labels_violation(reply: ReplyUnderReview) -> str | None:
    if reply.prose_word_count <= SHORT_CONFIRMATION_MAXIMUM_PROSE_WORDS:
        return None
    missing_labels = [
        label for label in REQUIRED_REPLY_LABELS if label not in reply.labels_present
    ]
    if not missing_labels:
        return None
    return (
        f"runs {reply.prose_word_count} prose words, past the "
        f"{SHORT_CONFIRMATION_MAXIMUM_PROSE_WORDS}-word confirmation, but omits the "
        + "/".join(f"{label}:" for label in missing_labels)
        + " label"
    )


def labeled_section_ceiling_violation(reply: ReplyUnderReview) -> str | None:
    if reply.labeled_section_word_count > LABELED_SECTION_WORD_CEILING:
        return (
            f"spends {reply.labeled_section_word_count} words under brief, done and "
            f"next, past their {LABELED_SECTION_WORD_CEILING}-word budget"
        )
    return None


def word_ceiling_violation(reply: ReplyUnderReview) -> str | None:
    if reply.prose_word_count > REPLY_HARD_WORD_CEILING:
        return (
            f"runs {reply.prose_word_count} prose words, a wall past the "
            f"{REPLY_HARD_WORD_CEILING}-word ceiling; move the detail into a table, "
            "tree or diagram, which is not counted"
        )
    return None


def list_block_length_violation(reply: ReplyUnderReview) -> str | None:
    for block in reply.list_blocks:
        if len(block) > MAXIMUM_LIST_BLOCK_LINES:
            return (
                f"stacks {len(block)} list lines, past the "
                f"{MAXIMUM_LIST_BLOCK_LINES}-line ceiling for one list"
            )
    return None


def list_line_word_violation(reply: ReplyUnderReview) -> str | None:
    for block in reply.list_blocks:
        for line in block:
            line_word_count = len(line.split())
            if line_word_count > MAXIMUM_LIST_LINE_WORDS:
                return (
                    f"runs a {line_word_count}-word list line, past the "
                    f"{MAXIMUM_LIST_LINE_WORDS}-word ceiling for one line"
                )
    return None
