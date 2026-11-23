from __future__ import annotations

import re

from ..document_fields import InvalidPeerDocument, require_bounded_line

HEARTBEAT_TITLE = "# Heartbeat"
HEARTBEAT_STATES = ("working", "waiting", "blocked", "done")
BLOCKED_STATE = "blocked"
LINE_FIELDS = (
    ("goal", "Goal"),
    ("done_when", "Done when"),
    ("state", "State"),
    ("doing", "Doing"),
    ("next", "Next"),
)
HEARTBEAT_LINE_LIMITS = {"goal": 80, "done_when": 200, "doing": 120, "next": 50}
LIST_SECTIONS = (
    ("done", "Done"),
    ("unverified", "Not verified"),
    ("open_decisions", "Open decisions"),
)
SECTION_PREFIX = "## "
ITEM_PREFIX = "- "
DONE_ITEM = re.compile(r"^(?P<claim>.+) \(evidence: (?P<evidence>[^()]+)\)$")
LINE_ADVICE = "keep it to a few words and put detail in a file"
HEARTBEAT_TEMPLATE = """# Heartbeat

Goal: <the outcome you own, at most 80 characters>
Done when: <the check that proves it, at most 200 characters>
State: <working | waiting | blocked | done>
Doing: <what you are doing right now, at most 120 characters>
Next: <your next step, at most 50 characters>

## Done

- <what you finished> (evidence: <commit, path, command or link>)

## Not verified

- <what you claim but have not checked>

## Open decisions

- <id of each decision card you filed that is still open>"""


def line_field(line: str, label: str) -> str:
    prefix = f"{label}:"
    if not line.startswith(prefix):
        raise InvalidPeerDocument(
            f"expected `{label}: ...` but found {line[:60]!r}; follow the template"
        )
    value = line[len(prefix) :].strip()
    if not value:
        raise InvalidPeerDocument(f"{label} must be nonempty")
    return value


def line_fields(lines: list[str]) -> dict:
    padded = lines + [""] * (len(LINE_FIELDS) - len(lines))
    return {
        field: line_field(line, label)
        for (field, label), line in zip(LINE_FIELDS, padded, strict=True)
    }


def section_lists(lines: list[str]) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    for line in lines:
        if line.startswith(SECTION_PREFIX):
            sections.append((line[len(SECTION_PREFIX) :].strip(), []))
        elif sections and line.startswith(ITEM_PREFIX):
            sections[-1][1].append(line[len(ITEM_PREFIX) :].strip())
        else:
            raise InvalidPeerDocument(
                f"{line[:60]!r} is neither a `## ` heading nor a `- ` item"
            )
    return sections


def done_item(item: str) -> dict:
    match = DONE_ITEM.match(item)
    evidence = match["evidence"].strip() if match else ""
    if not evidence:
        raise InvalidPeerDocument(
            f"Done item {item[:60]!r} must end with (evidence: <reference>) "
            "and the reference holds no parentheses"
        )
    return {"claim": match["claim"].strip(), "evidence": evidence}


def list_fields(lines: list[str]) -> dict:
    sections = section_lists(lines)
    titles = [title for title, _ in sections]
    expected = [title for _, title in LIST_SECTIONS]
    if titles != expected:
        raise InvalidPeerDocument(
            f"needs the sections {', '.join(expected)} in that order, found "
            f"{', '.join(titles) or 'none'}; leave a section empty rather than drop it"
        )
    items = {
        field: section[1]
        for (field, _), section in zip(LIST_SECTIONS, sections, strict=True)
    }
    return {**items, "done": [done_item(item) for item in items["done"]]}


def validated_heartbeat(heartbeat: dict) -> dict:
    for field, limit in HEARTBEAT_LINE_LIMITS.items():
        require_bounded_line(field, heartbeat[field], limit, LINE_ADVICE)
    if heartbeat["state"] not in HEARTBEAT_STATES:
        raise InvalidPeerDocument(
            f"State must be one of {' | '.join(HEARTBEAT_STATES)}"
        )
    if heartbeat["state"] == BLOCKED_STATE and not heartbeat["open_decisions"]:
        raise InvalidPeerDocument("a blocked heartbeat lists the decisions it waits on")
    return heartbeat


def parsed_heartbeat(text: str) -> dict:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines or lines[0] != HEARTBEAT_TITLE:
        raise InvalidPeerDocument(f"a heartbeat starts with the line {HEARTBEAT_TITLE}")
    field_count = len(LINE_FIELDS) + 1
    heartbeat = {
        **line_fields(lines[1:field_count]),
        **list_fields(lines[field_count:]),
    }
    return validated_heartbeat(heartbeat)


def item_lines(field: str, heartbeat: dict) -> list[str]:
    if field != "done":
        return [f"{ITEM_PREFIX}{item}" for item in heartbeat[field]]
    return [
        f"{ITEM_PREFIX}{item['claim']} (evidence: {item['evidence']})"
        for item in heartbeat["done"]
    ]


def rendered_heartbeat(heartbeat: dict) -> str:
    lines = [HEARTBEAT_TITLE, ""]
    lines += [f"{label}: {heartbeat[field]}" for field, label in LINE_FIELDS]
    for field, title in LIST_SECTIONS:
        items = item_lines(field, heartbeat)
        lines += ["", f"{SECTION_PREFIX}{title}", *([""] if items else []), *items]
    return "\n".join(lines)
