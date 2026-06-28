#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

hook_script_directory = Path(__file__).resolve().parent
shared_common_hook_modules_directory = hook_script_directory.parent / "common"
for importable_directory in (
    hook_script_directory,
    shared_common_hook_modules_directory,
):
    importable_directory_string = str(importable_directory)
    if importable_directory.is_dir() and importable_directory_string not in sys.path:
        sys.path.insert(0, importable_directory_string)

from end_of_turn_reply_template_rules import (  # noqa: E402
    COMPRESSION_GUIDANCE,
    template_violations_in_reply,
)
from interactive_session_detection import (  # noqa: E402
    is_keyboard_driven_interactive_session,
)


def read_hook_input_or_exit() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)


def user_prompt_text_from_event(transcript_event: dict) -> str:
    content = transcript_event.get("message", {}).get("content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ).strip()
    return ""


def read_final_turn_request_and_reply(transcript_path: str) -> tuple[str, str]:
    if not transcript_path or not os.path.exists(transcript_path):
        return "", ""
    current_turn_user_request = ""
    final_reply_text = ""
    with open(transcript_path, encoding="utf-8") as transcript_file:
        for transcript_line in transcript_file:
            transcript_line = transcript_line.strip()
            if not transcript_line:
                continue
            try:
                transcript_event = json.loads(transcript_line)
            except json.JSONDecodeError:
                continue
            event_kind = transcript_event.get("type")
            if event_kind == "user":
                final_reply_text = ""
                typed_request = user_prompt_text_from_event(transcript_event)
                if typed_request:
                    current_turn_user_request = typed_request
                continue
            if event_kind != "assistant":
                continue
            content_blocks = transcript_event.get("message", {}).get("content", [])
            if not isinstance(content_blocks, list):
                continue
            text_of_this_message = "".join(
                block.get("text", "")
                for block in content_blocks
                if isinstance(block, dict) and block.get("type") == "text"
            ).strip()
            if text_of_this_message:
                final_reply_text = text_of_this_message
    return current_turn_user_request, final_reply_text


def main() -> None:
    hook_input = read_hook_input_or_exit()
    if hook_input.get("hook_event_name", "") != "Stop":
        sys.exit(0)
    if not is_keyboard_driven_interactive_session():
        sys.exit(0)
    if hook_input.get("stop_hook_active"):
        sys.exit(0)

    user_request_text, reply_text = read_final_turn_request_and_reply(
        hook_input.get("transcript_path", "")
    )
    if not reply_text:
        sys.exit(0)

    violations = template_violations_in_reply(reply_text, user_request_text)
    if not violations:
        sys.exit(0)

    block_reason = (
        "End-of-turn reply breaks the enforced plain-prose template ("
        + "; ".join(violations)
        + "). "
        + COMPRESSION_GUIDANCE
    )
    print(json.dumps({"decision": "block", "reason": block_reason}))
    sys.exit(0)


if __name__ == "__main__":
    main()
