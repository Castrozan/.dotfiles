from __future__ import annotations

import re

STUB_KINDS = ("Tweet", "Youtube", "Article")
CLIPPED_TEXT_CHARACTER_LIMIT = 4000
KIND_LINE = re.compile(r"^\[\[ReadItLater\]\]\s+\[\[([^\]]+)\]\]")
LINK = re.compile(r"https?://[^\s)\]>\"'|]+")
STUB_LINE = re.compile(
    r"^(?:\[\[ReadItLater\]\]|#{1,6} \[|>|<iframe|#agent-work-done\b|[a-z_]+::"
    r"|\[https?://\S+\]\(https?://\S+\)$|!\[)"
)


def capture_kind(capture_body: str) -> str:
    first_line = next(iter(capture_body.lstrip().splitlines()), "")
    matched_kind = KIND_LINE.match(first_line)
    return matched_kind.group(1) if matched_kind else "Clipping"


def origin_url(capture_body: str) -> str | None:
    matched_link = LINK.search(capture_body)
    return matched_link.group(0) if matched_link else None


def is_stub_line(capture_line: str) -> bool:
    return bool(STUB_LINE.match(capture_line.strip()))


def lucas_note(capture_body: str) -> str:
    if capture_kind(capture_body) not in STUB_KINDS:
        return ""
    note_lines = [
        capture_line.strip()
        for capture_line in capture_body.splitlines()
        if capture_line.strip() and not is_stub_line(capture_line)
    ]
    return "\n".join(note_lines)


def clipped_text(capture_body: str) -> str:
    if capture_kind(capture_body) in STUB_KINDS:
        return ""
    return capture_body.strip()[:CLIPPED_TEXT_CHARACTER_LIMIT]
