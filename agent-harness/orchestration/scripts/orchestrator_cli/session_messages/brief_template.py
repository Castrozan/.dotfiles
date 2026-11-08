from __future__ import annotations

import re
from dataclasses import dataclass, field

TEMPLATE_HEADINGS = (
    "Goal",
    "Done when",
    "Constraints",
    "Workspace and worktree",
    "Lucas's words",
    "Contract",
)
QUOTED_HEADING = "Lucas's words"
CONTRACT_HEADING = "Contract"
CONTRACT_COMMANDS = ("orchestrator decision file --to", "orchestrator report file --to")
SECTION_HEADING = re.compile(r"^##\s+(?P<title>.+?)\s*$")
FENCE_MARKER = re.compile(r"^\s*(?P<fence>`{3,}|~{3,})")
ORDERED_STEPS = re.compile(
    r"^\s*(?:[-*+]\s+)?(?:\(?\d+[.)]|step\s+\d+[.:)]?)\s+\S"
    r"|(?:^|\s)\(?1\)\s.*\s\(?2\)\s",
    re.IGNORECASE,
)
AUTONOMY_ADVICE = (
    "number nothing outside Lucas's words: list outcomes as bullets and leave the "
    "order of work to the session"
)


@dataclass
class BriefSection:
    title: str
    prose_lines: list[tuple[int, str]] = field(default_factory=list)
    all_text: list[str] = field(default_factory=list)


def heading_key(title: str) -> str:
    return title.replace("’", "'").casefold()


def closes_fence(opening: str, line: str) -> bool:
    marker = FENCE_MARKER.match(line)
    return bool(
        marker
        and marker["fence"][0] == opening[0]
        and len(marker["fence"]) >= len(opening)
        and not line.strip()[len(marker["fence"]) :].strip()
    )


def brief_sections(text: str) -> list[BriefSection]:
    sections = [BriefSection("")]
    open_fence = None
    for number, line in enumerate(text.splitlines(), start=1):
        marker = FENCE_MARKER.match(line)
        if open_fence is not None:
            if closes_fence(open_fence, line):
                open_fence = None
            sections[-1].all_text.append(line)
            continue
        if marker:
            open_fence = marker["fence"]
            sections[-1].all_text.append(line)
            continue
        heading = SECTION_HEADING.match(line)
        if heading:
            sections.append(BriefSection(heading["title"]))
            continue
        sections[-1].all_text.append(line)
        sections[-1].prose_lines.append((number, line))
    return sections


def heading_problems(sections: list[BriefSection]) -> list[str]:
    remaining = iter(heading_key(section.title) for section in sections)
    missing = [
        title for title in TEMPLATE_HEADINGS if heading_key(title) not in remaining
    ]
    if not missing:
        return []
    expected = ", ".join(TEMPLATE_HEADINGS)
    return [
        f"needs the ## headings {expected} in that order; missing or out of order: {', '.join(missing)}"
    ]


def ordered_step_problems(sections: list[BriefSection]) -> list[str]:
    return [
        f"line {number} orders steps ({line.strip()[:40]!r}); {AUTONOMY_ADVICE}"
        for section in sections
        if heading_key(section.title) != heading_key(QUOTED_HEADING)
        for number, line in section.prose_lines
        if ORDERED_STEPS.search(line)
    ]


def contract_problems(
    sections: list[BriefSection], reply_host: str | None
) -> list[str]:
    contract = "\n".join(
        line
        for section in sections
        if heading_key(section.title) == heading_key(CONTRACT_HEADING)
        for line in section.all_text
    )
    required = [
        *CONTRACT_COMMANDS,
        *([f"--reply-host {reply_host}"] if reply_host else []),
    ]
    return [
        f"the Contract section must show the session `{command}`"
        for command in required
        if not re.search(re.escape(command) + r"(?!\S)", contract)
    ]


def brief_problems(text: str, reply_host: str | None) -> list[str]:
    sections = brief_sections(text)
    return [
        *heading_problems(sections),
        *ordered_step_problems(sections),
        *contract_problems(sections, reply_host),
    ]
