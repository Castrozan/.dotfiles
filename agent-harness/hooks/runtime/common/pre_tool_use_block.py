from __future__ import annotations

import json
import sys


def deny_pre_tool_use_call(block_message: str) -> None:
    output_payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": block_message,
        },
        "systemMessage": block_message,
    }
    json.dump(output_payload, sys.stdout)
    sys.exit(0)
