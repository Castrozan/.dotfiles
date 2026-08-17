#!/usr/bin/env python3

from __future__ import annotations

import re

from reply_text_metrics import ReplyUnderReview

TRACKABLE_ARTIFACT_REFERENCE_PATTERN = re.compile(
    r"\b(?:the|this|that)\s+(?:merge request|pull request)\b"
    r"|\bmerge request\s*!?\d+\b|\bpull request\s*#?\d+\b"
    r"|\bMR\s*!?\d+\b|\bPR\s*#?\d+\b",
    re.IGNORECASE,
)
URL_PRESENT_PATTERN = re.compile(r"https?://", re.IGNORECASE)


def unlinked_artifact_violation(reply: ReplyUnderReview) -> str | None:
    names_artifact = TRACKABLE_ARTIFACT_REFERENCE_PATTERN.search(reply.prose_text)
    if names_artifact and not URL_PRESENT_PATTERN.search(reply.prose_text):
        return "names an MR or PR but gives no link to validate it"
    return None
