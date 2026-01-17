#!/usr/bin/env python3
"""
Dangerous Command Blocker Hook
==============================
Blocks or warns about potentially dangerous shell commands.

Exit codes:
- 0: Allow command (optionally with warning via systemMessage)
- 2: Block command (message shown to Claude)
"""

import json
import re
import sys
from typing import Optional, Tuple

# Patterns that should be BLOCKED (exit 2)
BLOCKED_PATTERNS = [
    (r"rm\s+-rf\s+/(?!tmp|home|nix/store)", "BLOCKED: rm -rf on system directories"),
    (r"mkfs\.", "BLOCKED: filesystem formatting"),
    (r"dd\s+.*of=/dev/sd", "BLOCKED: writing to block devices"),
    (r":\s*\(\s*\)\s*\{\s*:\s*\|\s*:", "BLOCKED: fork bomb detected"),
    (r"curl.*\|\s*sh", "BLOCKED: piping curl to shell"),
    (r"wget.*\|\s*sh", "BLOCKED: piping wget to shell"),
]

# Patterns that should WARN but allow (exit 0 with systemMessage)
WARN_PATTERNS = [
    (r"rm\s+-rf", "WARNING: rm -rf detected - verify the path is correct"),
    (r"git\s+push\s+.*--force", "WARNING: Force pushing - this rewrites history"),
    (r"git\s+reset\s+--hard", "WARNING: Hard reset - uncommitted changes will be lost"),
    (r"chmod\s+777", "WARNING: chmod 777 is insecure - consider more restrictive permissions"),
    (r"sudo\s+rm", "WARNING: Deleting with sudo - verify the path"),
    (r"DROP\s+(TABLE|DATABASE)", "WARNING: Destructive SQL operation detected"),
    (r"TRUNCATE\s+TABLE", "WARNING: Truncating table will delete all data"),
]


def check_command(command: str) -> Tuple[bool, Optional[str]]:
    """
    Check command against patterns.
    Returns: (should_block, message)
    """
    # Check blocked patterns first
    for pattern, message in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, message

    # Check warning patterns
    for pattern, message in WARN_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, message

    return False, None


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    command = data.get("tool_input", {}).get("command", "")

    if not command:
        sys.exit(0)

    should_block, message = check_command(command)

    if should_block:
        print(message, file=sys.stderr)
        sys.exit(2)

    if message:
        # Warning - allow but show message
        output = {
            "continue": True,
            "systemMessage": message
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
