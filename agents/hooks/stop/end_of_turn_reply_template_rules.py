#!/usr/bin/env python3

from __future__ import annotations

import re

SHORT_CONFIRMATION_MAXIMUM_PROSE_LINES = 3
SCANNABLE_MAXIMUM_PROSE_LINES = 14
REPLY_TARGET_PROSE_WORDS = 150
REPLY_HARD_WORD_CEILING = 250
MAXIMUM_PROSE_PARAGRAPH_BLOCKS = 4

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

DONE_LABEL_PATTERN = re.compile(
    r"^\s*\*{0,2}done\*{0,2}\s*:", re.IGNORECASE | re.MULTILINE
)
NEXT_LABEL_PATTERN = re.compile(
    r"^\s*\*{0,2}next\*{0,2}\s*:", re.IGNORECASE | re.MULTILINE
)

LIST_MARKER_LINE_PATTERN = re.compile(r"^\s*([-*+]\s|\d+[.)]\s)")
MARKDOWN_HEADER_LINE_PATTERN = re.compile(r"^\s*#{1,6}\s")

TRACKABLE_ARTIFACT_REFERENCE_PATTERN = re.compile(
    r"\bmerge request\b|\bpull request\b|\bMR\s*!?\d+|\bPR\s*#?\d+",
    re.IGNORECASE,
)
URL_PRESENT_PATTERN = re.compile(r"https?://", re.IGNORECASE)

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

COMPRESSION_GUIDANCE = (
    "Rewrite it as a short, well-written plain-prose status report: open with a header-less "
    "paragraph that answers directly and gives the cause or context, then a **Done:** line and a "
    "**Next:** line in plain sentences. Aim for roughly "
    f"{REPLY_TARGET_PROSE_WORDS} words; a turn with real substance may run longer, and only a "
    f"genuine wall past {REPLY_HARD_WORD_CEILING} prose words is bounced, so keep the substance "
    "Lucas needs and cut only filler, never the answer. No bullet or numbered lists, no section "
    "headers, no reaction or narration openers, and no em dashes. When the work produced an MR, a "
    "PR, a ticket, an issue, or a deploy, include its link so Lucas can click through to validate "
    "it. If Lucas explicitly asked for a document or an in-detail write-up, keep its full length "
    "and structure, and note that fenced code blocks are already exempt from the count; but always "
    "drop em dashes and reaction or narration openers and link any MR or PR you name, because "
    "those still bounce a resend."
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


def user_request_permits_long_form(user_request_text: str) -> bool:
    if not user_request_text:
        return False
    return bool(
        LONG_FORM_ARTIFACT_REQUEST_PATTERN.search(user_request_text)
        or LONG_FORM_DIRECTIVE_PATTERN.search(user_request_text)
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

    prose_text = "\n".join(prose_lines_outside_code_fences(reply_text))
    if TRACKABLE_ARTIFACT_REFERENCE_PATTERN.search(
        prose_text
    ) and not URL_PRESENT_PATTERN.search(prose_text):
        violations.append("names an MR or PR but gives no link to validate it")

    return violations


def shape_and_length_violations(reply_text: str) -> list[str]:
    violations: list[str] = []
    prose_lines = prose_lines_outside_code_fences(reply_text)
    prose_word_count = sum(len(line.split()) for line in prose_lines)
    paragraph_block_count = prose_paragraph_block_count(reply_text)
    has_done_and_next_labels = bool(
        DONE_LABEL_PATTERN.search(reply_text) and NEXT_LABEL_PATTERN.search(reply_text)
    )

    if any(LIST_MARKER_LINE_PATTERN.match(line) for line in prose_lines):
        violations.append("uses a bullet or numbered list instead of prose")
    if any(MARKDOWN_HEADER_LINE_PATTERN.match(line) for line in prose_lines):
        violations.append("uses a section header")

    if (
        len(prose_lines) > SHORT_CONFIRMATION_MAXIMUM_PROSE_LINES
        and not has_done_and_next_labels
    ):
        violations.append(
            "longer than a confirmation but missing the **Done:**/**Next:** labels"
        )
    if len(prose_lines) > SCANNABLE_MAXIMUM_PROSE_LINES:
        violations.append(
            f"runs {len(prose_lines)} prose lines, past the "
            f"{SCANNABLE_MAXIMUM_PROSE_LINES}-line scannable cap"
        )
    if prose_word_count > REPLY_HARD_WORD_CEILING:
        violations.append(
            f"runs {prose_word_count} prose words, a wall past the "
            f"{REPLY_HARD_WORD_CEILING}-word hard ceiling"
        )
    if paragraph_block_count > MAXIMUM_PROSE_PARAGRAPH_BLOCKS:
        violations.append(
            f"stacks {paragraph_block_count} prose paragraphs, past the "
            f"{MAXIMUM_PROSE_PARAGRAPH_BLOCKS}-block ceiling of opening, Done, Next, and an "
            "optional Assumed line"
        )

    return violations


def template_violations_in_reply(
    reply_text: str, user_request_text: str = ""
) -> list[str]:
    violations = always_enforced_violations(reply_text)
    if user_request_permits_long_form(user_request_text):
        return violations
    violations.extend(shape_and_length_violations(reply_text))
    return violations
