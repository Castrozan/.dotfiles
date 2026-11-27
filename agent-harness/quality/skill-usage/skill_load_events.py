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


def typed_or_pinned_loads(blocks: list) -> Iterator[tuple[str, str]]:
    for block in blocks:
        if block.get("type") != "text":
            continue
        for slash, invoked_name in COMMAND_NAME.findall(block.get("text", "")):
            yield ("typed" if slash else "pinned"), invoked_name


def agent_or_nested_loads(blocks: list) -> Iterator[tuple[str, str]]:
    for block in blocks:
        if block.get("type") != "tool_use":
            continue
        tool_input = block.get("input") or {}
        if block.get("name") == "Skill":
            yield "agent", str(tool_input.get("skill", ""))
            continue
        if block.get("name") == "Read":
            nested = NESTED_SKILL_FILE.search(str(tool_input.get("file_path", "")))
            if nested:
                yield "nested", nested.group(1)


def human_prompt(record: dict) -> str | None:
    if record.get("isMeta") or record.get("isSidechain"):
        return None
    texts = [
        block.get("text", "")
        for block in content_blocks(record)
        if block.get("type") == "text"
    ]
    if not texts or any(
        block.get("type") == "tool_result" for block in content_blocks(record)
    ):
        return None
    prompt = " ".join(" ".join(texts).split())
    if not prompt or prompt.startswith("<"):
        return None
    return prompt[:PROMPT_EXCERPT_CHARACTERS]


def candidate_records(
    transcript_path: Path, markers: tuple[bytes, ...]
) -> Iterator[dict]:
    with transcript_path.open("rb") as transcript:
        for line in transcript:
            if not any(marker in line for marker in markers):
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if isinstance(record, dict):
                yield record


def transcript_skill_loads(
    transcript_path: Path, since: datetime, with_prompts: bool
) -> Iterator[SkillLoad]:
    markers = (*CANDIDATE_MARKERS, PROMPT_MARKER) if with_prompts else CANDIDATE_MARKERS
    latest_prompt: str | None = None
    for record in candidate_records(transcript_path, markers):
        record_type = record.get("type")
        if record_type == "user" and with_prompts:
            latest_prompt = human_prompt(record) or latest_prompt
        timestamp = record_timestamp(record)
        if timestamp is None or timestamp < since:
            continue
        session_identifier = str(record.get("sessionId", ""))
        if record_type == "user":
            for channel, invoked_name in typed_or_pinned_loads(content_blocks(record)):
                skill = catalogue_skill_name(invoked_name)
                if skill:
                    yield SkillLoad(skill, channel, session_identifier, timestamp, None)
        if record_type == "assistant":
            for channel, invoked_name in agent_or_nested_loads(content_blocks(record)):
                skill = catalogue_skill_name(invoked_name)
                if not skill:
                    continue
                prompt = latest_prompt if channel == "agent" else None
                yield SkillLoad(skill, channel, session_identifier, timestamp, prompt)


def skill_loads(
    projects_directory: Path, since: datetime, with_prompts: bool = False
) -> Iterator[SkillLoad]:
    since_epoch_seconds = since.timestamp()
    for transcript_path in sorted(projects_directory.rglob("*.jsonl")):
        if transcript_path.stat().st_mtime < since_epoch_seconds:
            continue
        yield from transcript_skill_loads(transcript_path, since, with_prompts)
