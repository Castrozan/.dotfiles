#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

hook_script_directory = Path(__file__).resolve().parent
shared_common_hook_modules_directory = hook_script_directory.parent / "common"
human_facing_reply_modules_directory = (
    shared_common_hook_modules_directory / "human_facing_reply"
)
for importable_directory in (
    hook_script_directory,
    shared_common_hook_modules_directory,
    human_facing_reply_modules_directory,
):
    importable_directory_string = str(importable_directory)
    if importable_directory.is_dir() and importable_directory_string not in sys.path:
        sys.path.insert(0, importable_directory_string)

from hook_dispatch import HandlerResult  # noqa: E402
from interactive_reply_reminder_state import (  # noqa: E402
    request_reply_reminder_rearm_after_drift,
)
from interactive_session_detection import (  # noqa: E402
    is_keyboard_driven_interactive_session,
)
from reply_rule_catalog import template_violations_in_reply  # noqa: E402
from reply_rule_rendering import rendered_bounce_guidance  # noqa: E402


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


def handle(hook_input: dict):
    if hook_input.get("hook_event_name", "") != "Stop":
        return None
    if not is_keyboard_driven_interactive_session():
        return None
    if hook_input.get("stop_hook_active"):
        return None

    user_request_text, reply_text = read_final_turn_request_and_reply(
        hook_input.get("transcript_path", "")
    )
    if not reply_text:
        return None

    violations = template_violations_in_reply(reply_text, user_request_text)
    if not violations:
        return None

    request_reply_reminder_rearm_after_drift(hook_input.get("session_id") or "")

    return HandlerResult(decision="block", reason=rendered_bounce_guidance(violations))
