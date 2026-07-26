#!/usr/bin/env python3

from __future__ import annotations

import re

from reply_template_shape_and_length_rules import (
    REPLY_HARD_WORD_CEILING,
    REPLY_TARGET_PROSE_WORDS,
    prose_lines_outside_code_fences,
    shape_and_length_violations,
    user_request_permits_long_form,
)

EM_DASH_CHARACTER = "—"

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

COMPRESSION_GUIDANCE = (
    "Rewrite it as a short, well-written plain-prose status report: open with a header-less "
    "paragraph that answers directly and gives the cause or context, then a **Done:** line and a "
    "**Next:** line in plain sentences. Aim for roughly "
    f"{REPLY_TARGET_PROSE_WORDS} words; a turn with real substance may run longer, and only a "
    f"genuine wall past {REPLY_HARD_WORD_CEILING} prose words is bounced, so keep the substance "
    "Lucas needs and cut only filler, never the answer. No bullet or numbered lists, no section "
    "headers, no reaction or narration openers, and no em dashes. Lucas reads only this "
    "end-of-turn message, so never point him at an earlier message ('as I said above', 'see my "
    "prior reply'); restate what still matters here so the reply stands alone. When the work "
    "produced an MR, a PR, a ticket, an issue, or a deploy, include its link so Lucas can click "
    "through to validate it. If Lucas explicitly asked for a document or an in-detail write-up, "
    "keep its full length and structure, and note that fenced code blocks are already exempt from "
    "the count; but always drop em dashes and reaction or narration openers, never defer to an "
    "earlier message, and link any MR or PR you name, because those still bounce a resend."
)


def always_enforced_violations(reply_text: str) -> list[str]:
    violations: list[str] = []
    reply_without_leading_space = reply_text.lstrip()

    if SYCOPHANCY_OR_REACTION_OPENER_PATTERN.match(reply_without_leading_space):
        violations.append("opens with a reaction or sycophancy phrase")
    if MECHANICS_NARRATION_OPENER_PATTERN.match(reply_without_leading_space):
        violations.append("opens by narrating what you are about to do")
    if EM_DASH_CHARACTER in reply_text:
        violations.append("contains an em dash")
    if REFERENCES_EARLIER_MESSAGE_PATTERN.search(reply_text):
        violations.append("defers to an earlier message instead of standing alone")

    prose_text = "\n".join(prose_lines_outside_code_fences(reply_text))
    if TRACKABLE_ARTIFACT_REFERENCE_PATTERN.search(
        prose_text
    ) and not URL_PRESENT_PATTERN.search(prose_text):
        violations.append("names an MR or PR but gives no link to validate it")

    return violations


def template_violations_in_reply(
    reply_text: str, user_request_text: str = ""
) -> list[str]:
    violations = always_enforced_violations(reply_text)
    if user_request_permits_long_form(user_request_text):
        return violations
    violations.extend(shape_and_length_violations(reply_text))
    return violations
