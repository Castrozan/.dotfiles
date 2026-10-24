import json
import os
import re
import sqlite3
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

from request_links import RequestLink, find_request_links
from review_command_runner import run_command

CLAUDE_PROJECTS_DIRECTORY = Path.home() / ".claude" / "projects"
CODEX_SESSIONS_DIRECTORY = Path.home() / ".codex" / "sessions"
OPENCODE_DATABASE = Path.home() / ".local" / "share" / "opencode" / "opencode.db"
SCREEN_LINES_READ = 400
REQUEST_LINK_MARKERS = ("merge_requests/", "/pull/")
CLAUDE_PROJECT_DIRECTORY_SEPARATOR = re.compile(r"[^A-Za-z0-9-]")


def entries_mentioning_requests(transcript: Path) -> Iterator[dict]:
    with transcript.open(encoding="utf-8", errors="replace") as transcript_lines:
        for line in transcript_lines:
            if not any(marker in line for marker in REQUEST_LINK_MARKERS):
                continue
            try:
                yield json.loads(line)
            except ValueError:
                continue


def is_main_assistant_entry(entry: dict) -> bool:
    return entry.get("type") == "assistant" and not entry.get("isSidechain")


def claude_text_blocks(content: str | list[dict]) -> list[str]:
    if isinstance(content, str):
        return [content]
    return [block["text"] for block in content if block["type"] == "text"]


def claude_reply_texts(session_id: str, agent_directory: str) -> list[str]:
    project_directory = CLAUDE_PROJECT_DIRECTORY_SEPARATOR.sub("-", agent_directory)
    transcript = CLAUDE_PROJECTS_DIRECTORY / project_directory / f"{session_id}.jsonl"
    if not transcript.exists():
        return []
    reply_texts = []
    for entry in entries_mentioning_requests(transcript):
        if is_main_assistant_entry(entry):
            reply_texts += claude_text_blocks(entry["message"]["content"])
    return reply_texts


def codex_reply_texts(session_id: str, _agent_directory: str) -> list[str]:
    transcript = next(
        iter(CODEX_SESSIONS_DIRECTORY.glob(f"*/*/*/rollout-*-{session_id}.jsonl")),
        None,
    )
    if transcript is None:
        return []
    reply_texts = []
    for entry in entries_mentioning_requests(transcript):
        payload = entry.get("payload", {})
        if entry.get("type") != "response_item" or payload.get("role") != "assistant":
            continue
        reply_texts += [
            block["text"]
            for block in payload.get("content", [])
            if block["type"] == "output_text"
        ]
    return reply_texts


def opencode_reply_texts(session_id: str, _agent_directory: str) -> list[str]:
    if not OPENCODE_DATABASE.exists():
        return []
    query = (
        "select part.data from part join message on message.id = part.message_id"
        " where part.session_id = ?"
        " and json_extract(message.data, '$.role') = 'assistant'"
        " and json_extract(part.data, '$.type') = 'text'"
        " order by part.time_created"
    )
    with closing(
        sqlite3.connect(f"file:{OPENCODE_DATABASE}?mode=ro", uri=True)
    ) as database:
        rows = database.execute(query, (session_id,)).fetchall()
    return [json.loads(part_data)["text"] for (part_data,) in rows]


REPLY_TEXT_READERS = {
    "claude": claude_reply_texts,
    "codex": codex_reply_texts,
    "opencode": opencode_reply_texts,
}


def screen_texts(pane_identifier: str) -> list[str]:
    result = run_command(
        [
            "herdr",
            "pane",
            "read",
            pane_identifier,
            "--source",
            "recent-unwrapped",
            "--lines",
            str(SCREEN_LINES_READ),
        ]
    )
    return result.stdout.splitlines() if result.returncode == 0 else []


def active_pane() -> dict | None:
    pane_identifier = os.environ.get("HERDR_ACTIVE_PANE_ID")
    if not pane_identifier:
        return None
    result = run_command(["herdr", "pane", "get", pane_identifier])
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)["result"]["pane"]


def agent_reply_texts(pane: dict) -> list[str]:
    agent_session = pane.get("agent_session") or {}
    read_reply_texts = REPLY_TEXT_READERS.get(agent_session.get("agent"))
    if read_reply_texts and agent_session.get("kind") == "id":
        reply_texts = read_reply_texts(agent_session["value"], pane.get("cwd", ""))
        if reply_texts:
            return reply_texts
    return screen_texts(pane["pane_id"])


def latest_request_link_in_active_agent() -> RequestLink | None:
    try:
        pane = active_pane()
        reply_texts = agent_reply_texts(pane) if pane else []
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error):
        return None
    for reply_text in reversed(reply_texts):
        request_links = find_request_links(reply_text)
        if request_links:
            return request_links[0]
    return None
