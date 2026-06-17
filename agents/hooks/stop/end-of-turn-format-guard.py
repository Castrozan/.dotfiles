#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from end_of_turn_reply_template_rules import (  # noqa: E402
    COMPRESSION_GUIDANCE,
    template_violations_in_reply,
)

INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE = "CLAUDE_INTERACTIVE_PREFERENCES_PATH"
CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER = "CLAWDE_RESUME_FLAG"


def is_clawde_background_agent_session() -> bool:
    return CLAWDE_BACKGROUND_AGENT_ENVIRONMENT_MARKER in os.environ


def is_keyboard_driven_interactive_session() -> bool:
    if is_clawde_background_agent_session():
        return False
    return bool(os.environ.get(INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE))


def read_hook_input_or_exit() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)


def read_final_assistant_reply_text(transcript_path: str) -> str:
    if not transcript_path or not os.path.exists(transcript_path):
        return ""
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
    return final_reply_text


def main() -> None:
    hook_input = read_hook_input_or_exit()
    if hook_input.get("hook_event_name", "") != "Stop":
        sys.exit(0)
    if not is_keyboard_driven_interactive_session():
        sys.exit(0)
    if hook_input.get("stop_hook_active"):
        sys.exit(0)

    reply_text = read_final_assistant_reply_text(hook_input.get("transcript_path", ""))
    if not reply_text:
        sys.exit(0)

    violations = template_violations_in_reply(reply_text)
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
