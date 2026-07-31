#!/usr/bin/env python3

from __future__ import annotations

import re

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
LONG_FORM_DESIGN_REQUEST_PATTERN = re.compile(
    r"\b(?:the\s+)?(?:design|architecture|technical\s+design|system\s+design)\s+"
    r"(?:of|for|behind)\s+the\b"
    r"|\b(?:design|architecture)\s+(?:doc|document|write-?up|proposal|"
    r"specification|spec)\b",
    re.IGNORECASE,
)


def user_request_permits_long_form(user_request_text: str) -> bool:
    if not user_request_text:
        return False
    return bool(
        LONG_FORM_ARTIFACT_REQUEST_PATTERN.search(user_request_text)
        or LONG_FORM_DIRECTIVE_PATTERN.search(user_request_text)
        or LONG_FORM_DESIGN_REQUEST_PATTERN.search(user_request_text)
    )
