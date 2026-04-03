#!/usr/bin/env python3

import json
import sys


def main():
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "unknown")

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "permissionDecision": "allow",
                "permissionDecisionReason": f"Auto-approved: {file_path}",
            }
        },
        sys.stdout,
    )


if __name__ == "__main__":
    main()
