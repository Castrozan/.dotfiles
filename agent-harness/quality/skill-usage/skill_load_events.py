from __future__ import annotations

import json
import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DOTFILES_PLUGIN_PREFIX = "dotfiles:"
CANDIDATE_MARKERS = (b'"name":"Skill"', b"/library/skills/", b"<command-name>")
PROMPT_MARKER = b'"role":"user","content":"'
COMMAND_NAME = re.compile(r"<command-name>(/?)([^<]+)</command-name>")
NESTED_SKILL_FILE = re.compile(r"/library/skills/([^/]+)/SKILL\.md$")
PROMPT_EXCERPT_CHARACTERS = 240


@dataclass(frozen=True)
class SkillLoad:
    skill: str
    channel: str
    session_identifier: str
    timestamp: datetime
    prompt: str | None


def catalogue_skill_name(invoked_name: str) -> str | None:
    name = invoked_name.strip().removeprefix("/")
    if ":" not in name:
        return name or None
    if name.startswith(DOTFILES_PLUGIN_PREFIX):
        return name.removeprefix(DOTFILES_PLUGIN_PREFIX) or None
    return None


def record_timestamp(record: dict) -> datetime | None:
    raw_timestamp = record.get("timestamp")
    if not isinstance(raw_timestamp, str):
        return None
    try:
        return datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None


def content_blocks(record: dict) -> list:
    content = (record.get("message") or {}).get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return content if isinstance(content, list) else []


def blocks_of_type(blocks: list, block_type: str) -> list[dict]:
    return [block for block in blocks if block.get("type") == block_type]


def typed_or_pinned_loads(blocks: list) -> list[tuple[str, str]]:
    return [
        ("typed" if slash else "pinned", invoked_name)
        for block in blocks_of_type(blocks, "text")
        for slash, invoked_name in COMMAND_NAME.findall(block.get("text", ""))
    ]


def tool_use_load(block: dict) -> tuple[str, str] | None:
    tool_input = block.get("input") or {}
    if block.get("name") == "Skill":
        return "agent", str(tool_input.get("skill", ""))
    nested = NESTED_SKILL_FILE.search(str(tool_input.get("file_path", "")))
    if block.get("name") == "Read" and nested:
        return "nested", nested.group(1)
    return None


def agent_or_nested_loads(blocks: list) -> list[tuple[str, str]]:
    return [
        load
        for block in blocks_of_type(blocks, "tool_use")
        if (load := tool_use_load(block))
    ]


def record_loads(record: dict) -> list[tuple[str, str]]:
    loads_by_record_type = {
        "user": typed_or_pinned_loads,
        "assistant": agent_or_nested_loads,
    }
    loads_of = loads_by_record_type.get(record.get("type"))
    return loads_of(content_blocks(record)) if loads_of else []


def is_human_turn(record: dict) -> bool:
    return (
        record.get("type") == "user"
        and not record.get("isMeta")
        and not record.get("isSidechain")
        and not blocks_of_type(content_blocks(record), "tool_result")
    )


def human_prompt(record: dict) -> str | None:
    if not is_human_turn(record):
        return None
    texts = [
        block.get("text", "")
        for block in blocks_of_type(content_blocks(record), "text")
    ]
    prompt = " ".join(" ".join(texts).split())
    if prompt.startswith("<"):
        return None
    return prompt[:PROMPT_EXCERPT_CHARACTERS] or None


def parsed_record(line: bytes) -> dict | None:
    try:
        record = json.loads(line)
    except ValueError:
        return None
    return record if isinstance(record, dict) else None


def candidate_records(
    transcript_path: Path, markers: tuple[bytes, ...]
) -> Iterator[dict]:
    with transcript_path.open("rb") as transcript:
        for line in transcript:
            record = (
                parsed_record(line)
                if any(marker in line for marker in markers)
                else None
            )
            if record:
                yield record


def record_skill_loads(
    record: dict, timestamp: datetime, latest_prompt: str | None
) -> Iterator[SkillLoad]:
    session_identifier = str(record.get("sessionId", ""))
    for channel, invoked_name in record_loads(record):
        skill = catalogue_skill_name(invoked_name)
        prompt = latest_prompt if channel == "agent" else None
        if skill:
            yield SkillLoad(skill, channel, session_identifier, timestamp, prompt)


def is_within_window(timestamp: datetime | None, since: datetime) -> bool:
    return timestamp is not None and timestamp >= since


def transcript_skill_loads(
    transcript_path: Path, since: datetime, markers: tuple[bytes, ...]
) -> Iterator[SkillLoad]:
    latest_prompt: str | None = None
    for record in candidate_records(transcript_path, markers):
        latest_prompt = human_prompt(record) or latest_prompt
        timestamp = record_timestamp(record)
        if is_within_window(timestamp, since):
            yield from record_skill_loads(record, timestamp, latest_prompt)


def skill_loads(
    projects_directory: Path, since: datetime, with_prompts: bool = False
) -> Iterator[SkillLoad]:
    markers = (*CANDIDATE_MARKERS, PROMPT_MARKER) if with_prompts else CANDIDATE_MARKERS
    since_epoch_seconds = since.timestamp()
    for transcript_path in sorted(projects_directory.rglob("*.jsonl")):
        if transcript_path.stat().st_mtime >= since_epoch_seconds:
            yield from transcript_skill_loads(transcript_path, since, markers)
