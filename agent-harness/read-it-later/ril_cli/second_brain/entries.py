from __future__ import annotations

import json
import re
from pathlib import Path

from second_brain.contract import SecondBrainContract
from second_brain.index import frontmatter_fields

FORBIDDEN_FILENAME_CHARACTERS = re.compile(r'[\\/:*?"<>|#^\[\]]')
FRONTMATTER_KEY = re.compile(r"^([\w-]+):", re.MULTILINE)
SECTION_HEADING = re.compile(r"^## (.+)$", re.MULTILINE)
LINK_SECTION_HEADING = "## By use"
FILED_STATUS = "filed"


def entry_file_name(title: str) -> str:
    return f"{FORBIDDEN_FILENAME_CHARACTERS.sub('-', title).strip()}.md"


def template_frontmatter_block(template_text: str) -> str:
    return template_text.split("---", 2)[1]


def frontmatter_line(key: str, value) -> str:
    if isinstance(value, list):
        return (
            "\n".join([f"{key}:", *(f"  - {item}" for item in value)])
            if value
            else f"{key}: []"
        )
    return f"{key}: {value}".rstrip()


def entry_values(template_defaults: dict, draft: dict, facts: dict) -> dict:
    return {
        **template_defaults,
        "title": json.dumps(draft["title"], ensure_ascii=False),
        "status": FILED_STATUS,
        "source-url": facts["source_url"],
        "creator": draft["creator"],
        "platform": draft["platform"],
        "captured": facts["captured"],
        "rating": "",
        "palette": [],
        "tags": draft["tags"],
    }


def entry_sections(draft: dict) -> dict:
    return {
        "Why it resonates": f"> {draft['why']}",
        "What to steal": "\n".join(f"- {item}" for item in draft["what_to_steal"]),
        "Reuse for": f"[[{draft['theme_moc']}]]: {draft['reuse_for']}",
    }


def render_entry(contract: SecondBrainContract, draft: dict, facts: dict) -> str:
    template = contract.template_text
    keys = FRONTMATTER_KEY.findall(template_frontmatter_block(template))
    values = entry_values(frontmatter_fields(template), draft, facts)
    frontmatter = "\n".join(frontmatter_line(key, values.get(key, "")) for key in keys)
    sections = entry_sections(draft)
    body = "\n\n".join(
        f"## {heading}\n{sections.get(heading, '')}"
        for heading in SECTION_HEADING.findall(template)
    )
    return f"---\n{frontmatter}\n---\n\n{body}\n"


def write_entry(contract: SecondBrainContract, draft: dict, facts: dict) -> Path:
    entry_path = contract.entry_directory / entry_file_name(draft["title"])
    if entry_path.exists():
        return entry_path
    entry_path.parent.mkdir(parents=True, exist_ok=True)
    entry_path.write_text(render_entry(contract, draft, facts), encoding="utf-8")
    return entry_path


def section_end(moc_text: str, heading_position: int) -> int:
    following_heading = re.compile(r"^#{1,2} ", re.MULTILINE).search(
        moc_text, heading_position + 1
    )
    return following_heading.start() if following_heading else len(moc_text)


def moc_with_link(moc_text: str, link_line: str) -> str:
    heading_position = moc_text.find(f"\n{LINK_SECTION_HEADING}\n")
    if heading_position < 0:
        return f"{moc_text.rstrip()}\n\n{LINK_SECTION_HEADING}\n{link_line}\n"
    insertion = section_end(moc_text, heading_position + 1)
    section = moc_text[:insertion].rstrip("\n")
    remainder = moc_text[insertion:]
    separator = "\n\n" if remainder else "\n"
    return f"{section}\n{link_line}{separator}{remainder}"


def link_into_moc(
    contract: SecondBrainContract, moc_title: str, entry_title: str, summary: str
) -> bool:
    moc_path = contract.atlas_directory / f"{moc_title}.md"
    moc_text = moc_path.read_text(encoding="utf-8")
    if f"[[{entry_title}]]" in moc_text:
        return False
    moc_path.write_text(
        moc_with_link(moc_text, f"- [[{entry_title}]]: {summary}"), encoding="utf-8"
    )
    return True
