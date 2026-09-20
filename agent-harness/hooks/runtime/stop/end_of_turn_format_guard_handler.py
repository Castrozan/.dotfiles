#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys

hook_script_directory = os.path.dirname(os.path.realpath(__file__))
shared_common_hook_modules_directory = os.path.join(
    os.path.dirname(hook_script_directory), "common"
)
human_facing_reply_modules_directory = os.path.join(
    shared_common_hook_modules_directory, "human_facing_reply"
)
for importable_directory in (
    hook_script_directory,
    shared_common_hook_modules_directory,
    human_facing_reply_modules_directory,
):
    if os.path.isdir(importable_directory) and importable_directory not in sys.path:
        sys.path.insert(0, importable_directory)

from hook_dispatch import HandlerResult  # noqa: E402
from interactive_session_detection import (  # noqa: E402
    is_keyboard_driven_interactive_session,
)
from reply_rule_catalog import template_violations_in_reply  # noqa: E402
from reply_rule_feedback import bounce_guidance  # noqa: E402


def text_from_content(content, accepted_block_types=("text",)) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") in accepted_block_types
        ).strip()
    return ""


def normalized_transcript_message(transcript_event: dict) -> tuple[str, str]:
    event_kind = transcript_event.get("type")
    if event_kind in ("user", "assistant"):
        message = transcript_event.get("message", {})
        return event_kind, text_from_content(message.get("content", ""))
    if event_kind != "response_item":
        return "", ""
    message = transcript_event.get("payload", {})
    if message.get("type") != "message":
        return "", ""
    role = message.get("role", "")
    if role == "user":
        return role, text_from_content(
            message.get("content", ""), ("input_text", "text")
        )
    if role == "assistant":
        return role, text_from_content(
            message.get("content", ""), ("output_text", "text")
        )
    return "", ""


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
            role, message_text = normalized_transcript_message(transcript_event)
            if role == "user":
                final_reply_text = ""
                if message_text:
                    current_turn_user_request = message_text
                continue
            if role != "assistant":
                continue
            if message_text:
                final_reply_text = message_text
    return current_turn_user_request, final_reply_text


def final_turn_request_and_reply(hook_input: dict) -> tuple[str, str]:
    transcript_request, transcript_reply = read_final_turn_request_and_reply(
        hook_input.get("transcript_path", "")
    )
    user_request_text = hook_input.get("user_request_text", "") or transcript_request
    reply_text = (
        hook_input.get("reply_text", "")
        or hook_input.get("last_assistant_message", "")
        or transcript_reply
    )
    return user_request_text.strip(), reply_text.strip()


def handle(hook_input: dict):
    if hook_input.get("hook_event_name", "") != "Stop":
        return None
    if not is_keyboard_driven_interactive_session():
        return None
    if hook_input.get("stop_hook_active"):
        return None

    user_request_text, reply_text = final_turn_request_and_reply(hook_input)
    if not reply_text:
        return None

    violations = template_violations_in_reply(reply_text, user_request_text)
    if not violations:
        return None

    return HandlerResult(decision="block", reason=bounce_guidance(violations))
