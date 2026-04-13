#!/usr/bin/env python3

import json
import sys

CRITICAL_RULES_REINFORCEMENT = """CORE INSTRUCTION REINFORCEMENT (post-compaction):

These rules are non-negotiable. They were loaded via CLAUDE.md -> AGENTS.md
at session start but may have been lost during context compaction.

1. NO COMMENTS: Zero comments in code. Names replace comments. Long descriptive
   function and variable names are the documentation.
2. WORKFLOW SEQUENCE: After editing any file in the dotfiles repo:
   format -> git add specific-file -> commit -> /rebuild -> tests/run.sh
   Do not respond to the user until rebuild succeeds and tests pass.
3. INVESTIGATE BEFORE FIXING: When asked to analyze or debug, gather evidence
   first. Read real files. Do not guess from memory. Analysis and implementation
   are separate phases.
4. SPECIFIC STAGING: Always git add specific-file. Never git add -A or git add .
5. PYTHON OVER BASH: Python 3.12 is default for scripts. Bash only for thin
   shell-native wrappers.
6. TEST FIRST: When a bug is reported, write a failing test first. The passing
   test proves the fix.
7. ANTI-SYCOPHANCY: When challenged, re-read the code before agreeing or
   disagreeing. Do not tone-match.
8. GLOB OVER FIND: Use Glob tool for file search, Read tool for file reading.
   Do not use Bash for cat, grep, find when dedicated tools exist.
9. CONCISE COMMUNICATION: Be direct. No em dashes. No preamble.

Full instructions: read the /core skill or AGENTS.md for complete rules."""


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    hook_event = data.get("hook_event_name", "")
    if hook_event != "PostCompact":
        sys.exit(0)

    output = {
        "continue": True,
        "systemMessage": CRITICAL_RULES_REINFORCEMENT,
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
