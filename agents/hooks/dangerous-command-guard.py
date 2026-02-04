#!/usr/bin/env python3
"""dangerous-command-guard.py - Block or warn about dangerous bash commands.

Exit codes:
  0 - Continue (with optional warning)
  2 - BLOCK the command (critical danger)
"""

import json
import re
import sys

# CRITICAL: These patterns are BLOCKED (exit 2) - could cause catastrophic data loss
BLOCKED_PATTERNS = [
    (r"rm\s+-rf\s+/\s*$", "BLOCKED: rm -rf / would destroy entire filesystem"),
    (r"rm\s+-rf\s+/\*", "BLOCKED: rm -rf /* would destroy entire filesystem"),
    (r"rm\s+-rf\s+~\s*$", "BLOCKED: rm -rf ~ would delete entire home directory"),
    (r"rm\s+-rf\s+\$HOME\s*$", "BLOCKED: rm -rf $HOME would delete entire home directory"),
    (r"dd\s+.*of=/dev/sd[a-z]\s*$", "BLOCKED: dd to raw disk would destroy all data"),
    (r"dd\s+.*of=/dev/nvme", "BLOCKED: dd to NVMe would destroy all data"),
    (r">\s*/dev/sd[a-z]", "BLOCKED: Direct write to block device destroys data"),
    (r"mkfs\.[a-z]+\s+/dev/sd[a-z][0-9]?\s*$", "BLOCKED: mkfs would format the partition"),
    (r":()\s*{\s*:\s*\|\s*:\s*&\s*}", "BLOCKED: Fork bomb detected"),
    (r"chmod\s+-R\s+777\s+/\s*$", "BLOCKED: chmod 777 / would break system security"),
    (r"chown\s+-R\s+.*\s+/\s*$", "BLOCKED: chown -R / could break system permissions"),
]

# DANGEROUS: Strong warning but not blocked (could cause significant damage)
DANGEROUS_PATTERNS = [
    (r"rm\s+-rf\s+\.", "Dangerous: rm -rf . deletes current directory recursively"),
    (r"rm\s+-rf\s+\.\.", "Dangerous: rm -rf .. deletes parent directory recursively"),
    (r"chmod\s+777\s+(/|~)", "Dangerous: Setting world-writable permissions"),
    (r"git\s+push\s+.*--force.*origin.*(main|master)", "Dangerous: Force push to main/master"),
    (r"git\s+reset\s+--hard\s+HEAD~\d+", "Dangerous: Hard reset discarding commits"),
    (r"DROP\s+(DATABASE|TABLE)", "Dangerous: Destructive database operation"),
    (r"truncate\s+.*-s\s*0\s+/", "Dangerous: Truncating system files"),
    (r"curl\s+.*\|\s*(sudo\s+)?bash", "Dangerous: Piping curl to bash is risky"),
    (r"wget\s+.*\|\s*(sudo\s+)?bash", "Dangerous: Piping wget to bash is risky"),
]

# WARNING: Less severe but worth noting
WARNING_PATTERNS = [
    (r"git\s+push\s+.*--force", "Warning: Force push can rewrite remote history"),
    (r"git\s+reset\s+--hard", "Warning: Hard reset discards uncommitted changes"),
    (r"rm\s+-rf\s+\S+", "Warning: Recursive force delete - verify the path"),
    (r"sudo\s+rm\s+-rf", "Warning: Sudo recursive delete - extra caution"),
    (r"nixos-rebuild\s+.*--upgrade", "Warning: System upgrade may break config"),
    (r"docker\s+system\s+prune\s+-a", "Warning: Will remove all unused Docker data"),
    (r"git\s+clean\s+-fdx", "Warning: Will delete untracked files/directories"),
]


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    command = data.get("tool_input", {}).get("command", "")

    if not command:
        sys.exit(0)

    # Check for BLOCKED patterns first - exit 2 stops the command
    for pattern, message in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            output = {
                "continue": False,
                "systemMessage": f"🛑 {message}\nCommand was blocked for safety."
            }
            print(json.dumps(output))
            sys.exit(2)  # EXIT 2 = BLOCK

    # Check for DANGEROUS patterns - strong warning but continue
    for pattern, message in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            output = {
                "continue": True,
                "systemMessage": f"⚠️  {message}\nCommand: {command.strip()}\nProceed with extreme caution!"
            }
            print(json.dumps(output))
            sys.exit(0)

    # Check for WARNING patterns
    warnings = []
    for pattern, message in WARNING_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            warnings.append(f"⚠️  {message}")

    if warnings:
        output = {
            "continue": True,
            "systemMessage": "\n".join(warnings)
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()