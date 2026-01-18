#!/usr/bin/env python3
"""dangerous-command-guard.py - Warn about potentially dangerous bash commands."""

import json
import re
import sys

# Patterns that could cause data loss or system damage
DANGEROUS_PATTERNS = [
    (r"rm\s+-rf\s+(/|~|\$HOME|\.)", "Dangerous recursive delete - verify path carefully"),
    (r"chmod\s+777\s+(/|~)", "Setting world-writable permissions on system directories"),
    (r">\s*/dev/sd[a-z]", "Direct write to block device - could destroy data"),
    (r"mkfs\.", "Filesystem creation - will destroy existing data"),
    (r"dd\s+.*of=/dev/", "Direct disk write - extremely dangerous"),
    (r"git\s+push\s+.*--force.*origin.*(main|master)", "Force push to main/master branch"),
    (r"git\s+reset\s+--hard\s+HEAD~\d+", "Hard reset discarding multiple commits"),
    (r"DROP\s+(DATABASE|TABLE)", "Destructive database operation"),
    (r"truncate\s+.*-s\s*0", "Truncating files to zero size"),
]

# Patterns that deserve a warning but aren't catastrophic
WARNING_PATTERNS = [
    (r"git\s+push\s+.*--force", "Force push can rewrite remote history"),
    (r"git\s+reset\s+--hard", "Hard reset discards uncommitted changes"),
    (r"rm\s+-rf\s+\S+", "Recursive force delete - double-check the path"),
    (r"sudo\s+rm\s+-rf", "Sudo recursive delete - extra caution needed"),
    (r"nixos-rebuild\s+.*--upgrade", "System upgrade - may break current config"),
    (r"docker\s+system\s+prune\s+-a", "Will remove all unused Docker images"),
    (r"git\s+clean\s+-fdx", "Will delete all untracked files and directories"),
]

def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    command = data.get("tool_input", {}).get("command", "")

    if not command:
        sys.exit(0)

    # Check for dangerous patterns first
    for pattern, message in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            output = {
                "continue": True,
                "systemMessage": f"⚠️  DANGER: {message}\nCommand: {command.strip()}"
            }
            print(json.dumps(output))
            sys.exit(0)

    # Check for warning patterns
    warnings = []
    for pattern, message in WARNING_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            warnings.append(f"⚠️  WARNING: {message}")

    if warnings:
        output = {
            "continue": True,
            "systemMessage": "\n".join(warnings)
        }
        print(json.dumps(output))

    sys.exit(0)

if __name__ == "__main__":
    main()