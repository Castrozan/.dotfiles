#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys

INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE = "CLAUDE_INTERACTIVE_PREFERENCES_PATH"

TLDR_REPLY_REMINDER = (
    "Reply as a TL;DR: lead with a one-line summary of the current state, then two short "
    "labeled parts, what was just done and what is next or still pending. Every reply, no "
    "exception, including short confirmations and mid-task updates. No preamble, no "
    "restating the request, no narration of mechanics."
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
