#!/usr/bin/env python3

import json
import shlex
import sys
from pathlib import Path

WORKSPACE_STATE_FILE = Path("/tmp/claude-code-workspace-cwd")


def read_target_workspace_directory():
    if not WORKSPACE_STATE_FILE.exists():
        return None
    content = WORKSPACE_STATE_FILE.read_text().strip()
    if not content:
        return None
    target = Path(content).expanduser()
    if not target.is_dir():
        return None
    return str(target.resolve())


def build_workspace_environment_prefix(workspace_directory):
    quoted_directory = shlex.quote(workspace_directory)
    return (
        f"cd {quoted_directory}"
        ' && { eval "$(direnv export bash 2>/dev/null)" 2>/dev/null || true; }'
    )


def main():
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    target_directory = read_target_workspace_directory()

    if not target_directory:
        sys.exit(0)

    original_command = hook_input.get("tool_input", {}).get("command", "")

    if not original_command:
        sys.exit(0)

    workspace_prefix = build_workspace_environment_prefix(target_directory)
    modified_command = f"{workspace_prefix} && {original_command}"

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "updatedInput": {
                "command": modified_command,
            },
        }
    }
    json.dump(output, sys.stdout)
    sys.exit(0)


if __name__ == "__main__":
    main()
