import json
from pathlib import Path

from .codex_rollout_lookup import CODEX_SESSIONS_DIRECTORY

CLAUDE_PROJECTS_DIRECTORY = Path.home() / ".claude" / "projects"


def transcript_path_for_session(
    harness_name: str,
    session_identifier: str,
    claude_projects_directory: Path = CLAUDE_PROJECTS_DIRECTORY,
    codex_sessions_directory: Path = CODEX_SESSIONS_DIRECTORY,
) -> Path | None:
    if harness_name == "claude":
        candidate_paths = sorted(
            claude_projects_directory.glob(f"*/{session_identifier}.jsonl")
        )
    elif harness_name == "codex":
        candidate_paths = sorted(
            codex_sessions_directory.rglob(f"rollout-*-{session_identifier}.jsonl")
        )
    else:
        candidate_paths = []
    return candidate_paths[0] if candidate_paths else None


def text_from_claude_message_content(message_content: object) -> str | None:
    if isinstance(message_content, str):
        return message_content
    if not isinstance(message_content, list):
        return None
    text_blocks = [
        block.get("text", "")
        for block in message_content
        if isinstance(block, dict) and block.get("type") == "text"
    ]
    joined_text = "\n".join(text for text in text_blocks if text)
    return joined_text or None


def claude_user_prompts(transcript_path: Path) -> list[str]:
    prompts = []
    with transcript_path.open(encoding="utf-8") as transcript_file:
        for transcript_line in transcript_file:
            try:
                record = json.loads(transcript_line)
            except json.JSONDecodeError:
                continue
            if record.get("type") != "user":
                continue
            if record.get("isSidechain") or record.get("isMeta"):
                continue
            message = record.get("message")
            if not isinstance(message, dict):
                continue
            prompt_text = text_from_claude_message_content(message.get("content"))
            if prompt_text:
                prompts.append(prompt_text)
    return prompts


def codex_user_prompts(transcript_path: Path) -> list[str]:
    prompts = []
    with transcript_path.open(encoding="utf-8") as transcript_file:
        for transcript_line in transcript_file:
            try:
                record = json.loads(transcript_line)
            except json.JSONDecodeError:
                continue
            payload = record.get("payload")
            if not isinstance(payload, dict):
                continue
            if payload.get("type") != "user_message":
                continue
            prompt_text = payload.get("message")
            if isinstance(prompt_text, str) and prompt_text:
                prompts.append(prompt_text)
    return prompts


def user_prompts_in_transcript(harness_name: str, transcript_path: Path) -> list[str]:
    if harness_name == "claude":
        return claude_user_prompts(transcript_path)
    if harness_name == "codex":
        return codex_user_prompts(transcript_path)
    return []
