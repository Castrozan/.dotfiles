"""Parse the Claude Code transcript to extract the current turn's user prompts and tool calls."""

import json
from pathlib import Path

MAX_PRIOR_USER_PROMPTS = 2
MAX_PRIOR_ASSISTANT_MESSAGES = 3
MAX_TOOL_RESULT_CHARS = 400


def read_transcript_entries(transcript_path: Path) -> list[dict]:
    if not transcript_path.exists():
        return []
    entries = []
    try:
        with open(transcript_path) as transcript_file:
            for line in transcript_file:
                stripped_line = line.strip()
                if not stripped_line:
                    continue
                try:
                    entries.append(json.loads(stripped_line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return entries


def extract_session_start_timestamp(entries: list[dict]) -> str:
    for entry in entries:
        timestamp = entry.get("timestamp", "")
        if isinstance(timestamp, str) and timestamp:
            return timestamp
    return ""


def flatten_tool_result_content(tool_result_content) -> str:
    if isinstance(tool_result_content, str):
        return tool_result_content
    if isinstance(tool_result_content, list):
        text_fragments: list[str] = []
        for block in tool_result_content:
            if not isinstance(block, dict):
                continue
            block_text = block.get("text")
            if isinstance(block_text, str):
                text_fragments.append(block_text)
        return "\n".join(text_fragments)
    return ""


def collect_tool_results_by_use_id(turn_entries: list[dict]) -> dict[str, str]:
    tool_results: dict[str, str] = {}
    for entry in turn_entries:
        if entry.get("type") != "user" or entry.get("isSidechain"):
            continue
        message = entry.get("message", {})
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") != "tool_result":
                continue
            use_id = block.get("tool_use_id")
            if not isinstance(use_id, str):
                continue
            flattened = flatten_tool_result_content(block.get("content"))
            tool_results[use_id] = flattened[:MAX_TOOL_RESULT_CHARS]
    return tool_results


def collect_prior_assistant_text(entries: list[dict], boundary_index: int) -> list[str]:
    prior_assistant_texts: list[str] = []
    for entry in entries[:boundary_index]:
        if entry.get("type") != "assistant" or entry.get("isSidechain"):
            continue
        message = entry.get("message", {})
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        text_pieces: list[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text":
                text_value = block.get("text", "").strip()
                if text_value:
                    text_pieces.append(text_value)
        if text_pieces:
            prior_assistant_texts.append("\n".join(text_pieces))
    return prior_assistant_texts[-MAX_PRIOR_ASSISTANT_MESSAGES:]


def find_last_user_prompt_boundary_index(entries: list[dict]) -> int:
    for index in range(len(entries) - 1, -1, -1):
        entry = entries[index]
        if entry.get("type") != "user":
            continue
        if entry.get("isSidechain"):
            continue
        message = entry.get("message", {})
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return index
    return -1


def collect_prior_user_prompts(entries: list[dict], boundary_index: int) -> list[str]:
    prior_prompts = []
    for entry in entries[:boundary_index]:
        if entry.get("type") != "user" or entry.get("isSidechain"):
            continue
        message = entry.get("message", {})
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            prior_prompts.append(content.strip())
    return prior_prompts[-MAX_PRIOR_USER_PROMPTS:]


def extract_current_turn_context_from_transcript(transcript_path: Path) -> dict:
    entries = read_transcript_entries(transcript_path)
    if not entries:
        return {}

    boundary_index = find_last_user_prompt_boundary_index(entries)
    if boundary_index < 0:
        return {}

    prior_user_prompts = collect_prior_user_prompts(entries, boundary_index)
    prior_assistant_messages = collect_prior_assistant_text(entries, boundary_index)
    session_start_timestamp = extract_session_start_timestamp(entries)

    current_turn_entries = entries[boundary_index:]
    current_user_prompts: list[str] = []
    ordered_tool_calls: list[dict] = []
    assistant_text_blocks: list[str] = []
    workspace_cwd = ""

    for entry in current_turn_entries:
        if entry.get("isSidechain"):
            continue
        if not workspace_cwd:
            workspace_cwd = entry.get("cwd", "")

        entry_type = entry.get("type")
        message = entry.get("message", {})
        if not isinstance(message, dict):
            continue
        content = message.get("content")

        if entry_type == "user" and isinstance(content, str) and content.strip():
            current_user_prompts.append(content.strip())
            continue

        if entry_type == "assistant" and isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                block_type = block.get("type")
                if block_type == "tool_use":
                    ordered_tool_calls.append(block)
                elif block_type == "text":
                    text_value = block.get("text", "").strip()
                    if text_value:
                        assistant_text_blocks.append(text_value)

    tool_results_by_use_id = collect_tool_results_by_use_id(current_turn_entries)

    return {
        "prior_user_prompts": prior_user_prompts,
        "prior_assistant_messages": prior_assistant_messages,
        "current_user_prompts": current_user_prompts,
        "ordered_tool_calls": ordered_tool_calls,
        "tool_results_by_use_id": tool_results_by_use_id,
        "assistant_text": "\n\n".join(assistant_text_blocks),
        "workspace_cwd": workspace_cwd,
        "session_start_timestamp": session_start_timestamp,
    }


def has_any_file_mutating_tool_call(ordered_tool_calls: list[dict]) -> bool:
    mutating_tool_names = {"Edit", "Write", "NotebookEdit", "Update"}
    for tool_call_block in ordered_tool_calls:
        if tool_call_block.get("name") in mutating_tool_names:
            return True
    return False
