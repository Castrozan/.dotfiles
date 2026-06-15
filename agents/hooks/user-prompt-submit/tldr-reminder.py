#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys

INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE = "CLAUDE_INTERACTIVE_PREFERENCES_PATH"

TLDR_REPLY_REMINDER = (
    "Reply as a TL;DR status report in the enforced shape: line one answers the question or "
    "states the current state in one sentence, then a `**Done:**` line and a `**Next:**` line, "
    "each at most three bullets; a one or two line confirmation may be line one alone. "
    'No reaction or sycophancy openers, no mechanics narration ("Let me", "I\'ll go ahead"), '
    "no essay sections beyond those labels, no em dashes, no pasted file contents or command "
    "output. A Stop hook bounces one reply per turn that opens with a reaction or narration "
    "phrase, uses an em dash, drops the labels, or runs long."
)


def read_hook_input_or_exit() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)


def main() -> None:
    hook_input = read_hook_input_or_exit()

    if hook_input.get("hook_event_name", "") != "UserPromptSubmit":
        sys.exit(0)

    if not os.environ.get(INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE):
        sys.exit(0)

    output = {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": TLDR_REPLY_REMINDER,
        },
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
