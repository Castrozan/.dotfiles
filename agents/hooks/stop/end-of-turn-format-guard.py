#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import re
import sys

INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE = "CLAUDE_INTERACTIVE_PREFERENCES_PATH"

SHORT_CONFIRMATION_MAXIMUM_PROSE_LINES = 3
SCANNABLE_MAXIMUM_PROSE_LINES = 14
SCANNABLE_MAXIMUM_PROSE_WORDS = 250

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

COMPRESSION_GUIDANCE = (
    "Rewrite it as a short, well-written plain-prose status report: open with a header-less "
    "paragraph that answers directly and gives the cause or context so Lucas understands it "
    "fully, then a **Done:** line and a **Next:** line in plain sentences. No bullet or numbered "
    "lists, no section headers, no reaction or narration openers, and no em dashes. When the work "
    "produced an MR, a PR, a ticket, an issue, or a deploy, include its link so Lucas can click "
    "through to validate it. If Lucas explicitly asked for a document or code, resend it "
    "unchanged and it will pass."
)


def read_hook_input_or_exit() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)


def read_final_assistant_reply_text(transcript_path: str) -> str:
    if not transcript_path or not os.path.exists(transcript_path):
        return ""
    final_reply_text = ""
    with open(transcript_path, encoding="utf-8") as transcript_file:
        for transcript_line in transcript_file:
            transcript_line = transcript_line.strip()
            if not transcript_line:
                continue
            try:
                transcript_event = json.loads(transcript_line)
            except json.JSONDecodeError:
                continue
            event_kind = transcript_event.get("type")
            if event_kind == "user":
                final_reply_text = ""
                continue
            if event_kind != "assistant":
                continue
            content_blocks = transcript_event.get("message", {}).get("content", [])
            if not isinstance(content_blocks, list):
                continue
            text_of_this_message = "".join(
                block.get("text", "")
                for block in content_blocks
                if isinstance(block, dict) and block.get("type") == "text"
            ).strip()
            if text_of_this_message:
                final_reply_text = text_of_this_message
    return final_reply_text


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


def template_violations_in_reply(reply_text: str) -> list[str]:
    violations: list[str] = []
    reply_without_leading_space = reply_text.lstrip()

    if SYCOPHANCY_OR_REACTION_OPENER_PATTERN.match(reply_without_leading_space):
        violations.append("opens with a reaction or sycophancy phrase")
    if MECHANICS_NARRATION_OPENER_PATTERN.match(reply_without_leading_space):
        violations.append("opens by narrating what you are about to do")
    if EM_DASH_CHARACTER in reply_text:
        violations.append("contains an em dash")

    prose_lines = prose_lines_outside_code_fences(reply_text)
    prose_word_count = sum(len(line.split()) for line in prose_lines)
    has_done_and_next_labels = bool(
        DONE_LABEL_PATTERN.search(reply_text) and NEXT_LABEL_PATTERN.search(reply_text)
    )

    if any(LIST_MARKER_LINE_PATTERN.match(line) for line in prose_lines):
        violations.append("uses a bullet or numbered list instead of prose")
    if any(MARKDOWN_HEADER_LINE_PATTERN.match(line) for line in prose_lines):
        violations.append("uses a section header")
    prose_text = "\n".join(prose_lines)
    if TRACKABLE_ARTIFACT_REFERENCE_PATTERN.search(
        prose_text
    ) and not URL_PRESENT_PATTERN.search(prose_text):
        violations.append("names an MR or PR but gives no link to validate it")

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
    if prose_word_count > SCANNABLE_MAXIMUM_PROSE_WORDS:
        violations.append(
            f"runs {prose_word_count} prose words, past the "
            f"{SCANNABLE_MAXIMUM_PROSE_WORDS}-word scannable cap"
        )

    return violations


def main() -> None:
    hook_input = read_hook_input_or_exit()
    if hook_input.get("hook_event_name", "") != "Stop":
        sys.exit(0)
    if not os.environ.get(INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE):
        sys.exit(0)
    if hook_input.get("stop_hook_active"):
        sys.exit(0)

    reply_text = read_final_assistant_reply_text(hook_input.get("transcript_path", ""))
    if not reply_text:
        sys.exit(0)

    violations = template_violations_in_reply(reply_text)
    if not violations:
        sys.exit(0)

    block_reason = (
        "End-of-turn reply breaks the enforced plain-prose template ("
        + "; ".join(violations)
        + "). "
        + COMPRESSION_GUIDANCE
    )
    print(json.dumps({"decision": "block", "reason": block_reason}))
    sys.exit(0)


if __name__ == "__main__":
    main()
