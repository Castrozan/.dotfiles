#!/usr/bin/env python3

from __future__ import annotations

import re

from reply_template_limits import (
    MAXIMUM_PROSE_PARAGRAPH_BLOCKS,
    REPLY_HARD_CHARACTER_CEILING,
    REPLY_HARD_WORD_CEILING,
    SHORT_CONFIRMATION_MAXIMUM_PROSE_WORDS,
)
from reply_text_metrics import ReplyUnderReview

EM_DASH_CHARACTER = "—"
EN_DASH_CHARACTER = "–"

LIST_MARKER_LINE_PATTERN = re.compile(r"^\s*([-*+]\s|\d+[.)]\s)")
MARKDOWN_HEADER_LINE_PATTERN = re.compile(r"^\s*#{1,6}\s")

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

REFERENCES_EARLIER_MESSAGE_PATTERN = re.compile(
    r"(?:my|the)\s+(?:prior|previous|earlier|last|preceding|above)\s+"
    r"(?:message|reply|turn|response|answer|note)"
    r"|as\s+i\s+(?:said|mentioned|noted|stated|explained|described|wrote|outlined|"
    r"covered|laid\s+out)\s+(?:above|earlier|before|previously)"
    r"|(?:see|per|from|in)\s+(?:my|the)\s+(?:prior|previous|earlier|last|preceding|"
    r"above)\s+(?:message|reply|turn|response|note)",
    re.IGNORECASE,
)

TRACKABLE_ARTIFACT_REFERENCE_PATTERN = re.compile(
    r"\bmerge request\b|\bpull request\b|\bMR\s*!?\d+|\bPR\s*#?\d+",
    re.IGNORECASE,
)
URL_PRESENT_PATTERN = re.compile(r"https?://", re.IGNORECASE)


def sentence_dash_violation(reply: ReplyUnderReview) -> str | None:
    if EM_DASH_CHARACTER in reply.prose_text:
        return "contains an em dash"
    if EN_DASH_CHARACTER in reply.prose_text:
        return "contains an en dash"
    return None


def reaction_opener_violation(reply: ReplyUnderReview) -> str | None:
    if SYCOPHANCY_OR_REACTION_OPENER_PATTERN.match(reply.text_without_leading_space):
        return "opens with a reaction or sycophancy phrase"
    return None


def narration_opener_violation(reply: ReplyUnderReview) -> str | None:
    if MECHANICS_NARRATION_OPENER_PATTERN.match(reply.text_without_leading_space):
        return "opens by narrating what you are about to do"
    return None


def earlier_message_deferral_violation(reply: ReplyUnderReview) -> str | None:
    if REFERENCES_EARLIER_MESSAGE_PATTERN.search(reply.text):
        return "defers to an earlier message instead of standing alone"
    return None


def unlinked_artifact_violation(reply: ReplyUnderReview) -> str | None:
    names_artifact = TRACKABLE_ARTIFACT_REFERENCE_PATTERN.search(reply.prose_text)
    if names_artifact and not URL_PRESENT_PATTERN.search(reply.prose_text):
        return "names an MR or PR but gives no link to validate it"
    return None


def bullet_or_numbered_list_violation(reply: ReplyUnderReview) -> str | None:
    if any(LIST_MARKER_LINE_PATTERN.match(line) for line in reply.prose_lines):
        return "uses a bullet or numbered list instead of prose"
    return None


def section_header_violation(reply: ReplyUnderReview) -> str | None:
    if any(MARKDOWN_HEADER_LINE_PATTERN.match(line) for line in reply.prose_lines):
        return "uses a section header"
    return None


def missing_done_and_next_labels_violation(reply: ReplyUnderReview) -> str | None:
    if (
        reply.prose_word_count > SHORT_CONFIRMATION_MAXIMUM_PROSE_WORDS
        and not reply.has_done_and_next_labels
    ):
        return "longer than a confirmation but missing the **Done:**/**Next:** labels"
    return None


def word_ceiling_violation(reply: ReplyUnderReview) -> str | None:
    if reply.prose_word_count > REPLY_HARD_WORD_CEILING:
        return (
            f"runs {reply.prose_word_count} prose words, a wall past the "
            f"{REPLY_HARD_WORD_CEILING}-word hard ceiling"
        )
    return None


def character_ceiling_violation(reply: ReplyUnderReview) -> str | None:
    if reply.prose_character_count > REPLY_HARD_CHARACTER_CEILING:
        return (
            f"runs {reply.prose_character_count} prose characters, a wall past the "
            f"{REPLY_HARD_CHARACTER_CEILING}-character hard ceiling"
        )
    return None


def paragraph_block_ceiling_violation(reply: ReplyUnderReview) -> str | None:
    if reply.paragraph_block_count > MAXIMUM_PROSE_PARAGRAPH_BLOCKS:
        return (
            f"stacks {reply.paragraph_block_count} prose paragraphs, past the "
            f"{MAXIMUM_PROSE_PARAGRAPH_BLOCKS}-block ceiling of opening, Done, Next, and an "
            "optional Assumed line"
        )
    return None
