#!/usr/bin/env python3

from __future__ import annotations

import json
import sys

POST_COMPACTION_RECOVERY_DIRECTIVE = (
    "POST-COMPACTION RECOVERY: the conversation was just summarized, so re-read any "
    "active HEARTBEAT.md or .deep-work/*/PLAN.md tracker on disk and restore the durable "
    "state before continuing: the deep-work path and plan phase, the user's requirements, "
    "the files already modified, the test and rebuild results, the key decisions, and the "
    "pre-work git SHA. Verbose tool outputs and raw research dumps are droppable; do not "
    "reconstruct them."
)


def read_hook_input_or_exit() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)


def main() -> None:
    hook_input = read_hook_input_or_exit()

    if hook_input.get("hook_event_name", "") != "SessionStart":
        sys.exit(0)

    if hook_input.get("source", "") != "compact":
        sys.exit(0)

    output = {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": POST_COMPACTION_RECOVERY_DIRECTIVE,
        },
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
