#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys

INTERACTIVE_SESSION_ENVIRONMENT_VARIABLE = "CLAUDE_INTERACTIVE_PREFERENCES_PATH"

TLDR_REPLY_REMINDER = (
    "Reply as a short, well-written status report in plain prose, no lists and no numbering. "
    "Open with a header-less paragraph that answers directly and gives the cause or context so "
    "Lucas understands it fully, then a `**Done:**` line and a `**Next:**` line, each one or two "
    "plain sentences; a one or two sentence confirmation may be the opening paragraph alone. "
    'No reaction or sycophancy openers, no mechanics narration ("Let me", "I\'ll go ahead"), no '
    "section headers, no repeated content, no em dashes, no pasted output. Full context comes "
    "from complete prose, not length. A Stop hook bounces one reply per turn that breaks this."
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
