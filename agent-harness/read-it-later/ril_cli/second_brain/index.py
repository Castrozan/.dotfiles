from __future__ import annotations

import os
import re
from pathlib import Path

SECOND_BRAIN_DIRECTORY_NAME = "Second Brain"
ATLAS_DIRECTORY_NAME = "Atlas"
ENTRY_DIRECTORY_NAME = "Inspiration"
MOC_SUFFIX = " MOC"
FRONTMATTER = re.compile(r"\A---\n(?P<block>.*?)\n---\n", re.DOTALL)
SCALAR_LINE = re.compile(r"^(?P<key>[\w-]+):\s*(?P<value>.*)$")
LIST_ITEM_LINE = re.compile(r"^\s+-\s+(?P<item>.+)$")
WIKILINK = re.compile(r"\[\[([^\]|#]+)")


def default_vault_directory() -> Path:
    return Path(os.environ.get("OBSIDIAN_HOME") or Path.home() / "vault")


def second_brain_directory(vault_directory: Path) -> Path:
    return vault_directory / SECOND_BRAIN_DIRECTORY_NAME


def unquoted(value: str) -> str:
    return value.strip().strip('"').strip("'")


def appended_item(fields: dict, key: str, item: str) -> list[str]:
    existing = fields.get(key)
    return [*(existing if isinstance(existing, list) else []), unquoted(item)]


def frontmatter_lines(note_text: str) -> list[str]:
    matched_block = FRONTMATTER.match(note_text)
    return matched_block.group("block").splitlines() if matched_block else []


def frontmatter_fields(note_text: str) -> dict:
    fields: dict = {}
    current_key = ""
    for block_line in frontmatter_lines(note_text):
        scalar = SCALAR_LINE.match(block_line)
        item = LIST_ITEM_LINE.match(block_line)
        if scalar:
            current_key = scalar.group("key")
            fields[current_key] = unquoted(scalar.group("value"))
        elif item and current_key:
            fields[current_key] = appended_item(fields, current_key, item.group("item"))
    return fields


def topic_tag(fields: dict) -> str:
    tags = fields.get("tags")
    return (
        next((tag for tag in tags if tag.startswith("topic/")), "")
        if isinstance(tags, list)
        else ""
    )


def theme_moc(note_text: str) -> str:
    body = FRONTMATTER.sub("", note_text, count=1)
    linked = [
        link.strip()
        for link in WIKILINK.findall(body)
        if link.strip().endswith(MOC_SUFFIX)
    ]
    return linked[0] if linked else ""


def entry_record(second_brain: Path, entry_path: Path) -> dict:
    note_text = entry_path.read_text(encoding="utf-8", errors="replace")
    fields = frontmatter_fields(note_text)
    return {
        "title": entry_path.stem,
        "path": str(entry_path.relative_to(second_brain)),
        "theme": theme_moc(note_text) or topic_tag(fields),
        "source_url": fields.get("source-url") or "",
    }


def entry_records(vault_directory: Path) -> list[dict]:
    second_brain = second_brain_directory(vault_directory)
    entry_directory = second_brain / ENTRY_DIRECTORY_NAME
    if not entry_directory.is_dir():
        return []
    return [
        entry_record(second_brain, entry_path)
        for entry_path in sorted(entry_directory.rglob("*.md"))
    ]


def moc_titles(vault_directory: Path) -> list[str]:
    atlas = second_brain_directory(vault_directory) / ATLAS_DIRECTORY_NAME
    if not atlas.is_dir():
        return []
    return sorted(path.stem for path in atlas.glob(f"*{MOC_SUFFIX}.md"))


def second_brain_index(vault_directory: Path) -> dict:
    return {
        "mocs": moc_titles(vault_directory),
        "entries": entry_records(vault_directory),
    }


def entries_matching_origin(
    entries: list[dict], origin_url: str | None, origin_id: str
) -> list[dict]:
    needles = [needle for needle in (origin_id, origin_url) if needle]
    return [
        entry
        for entry in entries
        if entry["source_url"]
        and any(needle in entry["source_url"] for needle in needles)
    ]
