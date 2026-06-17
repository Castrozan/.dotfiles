#!/usr/bin/env python3

from __future__ import annotations

import json
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

from interactive_session_detection import (  # noqa: E402
    is_keyboard_driven_interactive_session,
)

TLDR_REPLY_REMINDER = (
    "Reply as a short, well-written status report in plain prose, no lists and no numbering. "
    "Open with a header-less paragraph that answers directly and gives the cause or context so "
    "Lucas understands it fully, then a `**Done:**` line and a `**Next:**` line, each one or two "
    "plain sentences; a one or two sentence confirmation may be the opening paragraph alone. "
    "Keep the whole reply under roughly 150 words and to that shape, an opening paragraph plus a "
    "Done and Next of one or two lines each, never a multi-paragraph dump and never a Done or "
    "Next that swells into several paragraphs. "
    'No reaction or sycophancy openers, no mechanics narration ("Let me", "I\'ll go ahead"), no '
    "section headers, no repeated content, no em dashes, no pasted output. Include the link to "
    "any MR, PR, ticket, issue, or deploy the work produced so Lucas can validate it. Full "
    "context comes from well-chosen prose, not length. A Stop hook bounces one reply per turn "
    "that breaks this or runs past roughly 150 words."
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

    if not is_keyboard_driven_interactive_session():
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
