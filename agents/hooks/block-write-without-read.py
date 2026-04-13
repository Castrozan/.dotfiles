#!/usr/bin/env python3

import json
import sys
from pathlib import Path


def load_hook_input() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)


def extract_target_file_path_from_tool_input(hook_payload: dict) -> str | None:
    tool_input = hook_payload.get("tool_input") or {}
    raw_path = tool_input.get("file_path")
    if not raw_path:
        return None
    return raw_path


def target_file_already_exists_on_disk(target_path: str) -> bool:
    try:
        return Path(target_path).is_file()
    except OSError:
        return False


def load_session_transcript_lines(hook_payload: dict) -> list[str]:
    transcript_path_value = hook_payload.get("transcript_path")
    if not transcript_path_value:
        return []
    transcript_file = Path(transcript_path_value)
    if not transcript_file.is_file():
        return []
    try:
        return transcript_file.read_text().splitlines()
    except OSError:
        return []


def was_target_file_read_in_this_session(
    target_path: str, transcript_lines: list[str]
) -> bool:
    for transcript_line in transcript_lines:
        try:
            parsed = json.loads(transcript_line)
        except json.JSONDecodeError:
            continue
        message = parsed.get("message") or {}
        content = message.get("content") or []
        if not isinstance(content, list):
            continue
        for content_block in content:
            if not isinstance(content_block, dict):
                continue
            if content_block.get("type") != "tool_use":
                continue
            if content_block.get("name") != "Read":
                continue
            read_input = content_block.get("input") or {}
            if read_input.get("file_path") == target_path:
                return True
    return False


def deny_with_reminder(target_path: str) -> dict:
    reason = (
        f"Read {target_path} before writing to it. "
        "The file exists on disk and has not been Read in this session. "
        "Grep snippets are not enough context to overwrite safely. "
        "Call Read first, then re-issue the Write."
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def main():
    hook_payload = load_hook_input()

    tool_name = hook_payload.get("tool_name", "")
    if tool_name not in ("Write", "Edit"):
        sys.exit(0)

    target_path = extract_target_file_path_from_tool_input(hook_payload)
    if not target_path:
        sys.exit(0)

    if not target_file_already_exists_on_disk(target_path):
        sys.exit(0)

    transcript_lines = load_session_transcript_lines(hook_payload)
    if not transcript_lines:
        sys.exit(0)

    if was_target_file_read_in_this_session(target_path, transcript_lines):
        sys.exit(0)

    print(json.dumps(deny_with_reminder(target_path)))
    sys.exit(0)


if __name__ == "__main__":
    main()
