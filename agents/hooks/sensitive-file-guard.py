#!/usr/bin/env python3
"""
Sensitive File Guard Hook
=========================
Warns or blocks when editing files that may contain secrets.
"""

import json
import re
import sys
from pathlib import Path

# Files that should be BLOCKED from editing
BLOCKED_FILES = [
    r"\.ssh/.*",
    r"\.gnupg/.*",
    r".*\.pem$",
    r".*\.key$",
    r"id_rsa",
    r"id_ed25519",
]

# Files that should show a WARNING
WARN_FILES = [
    r"\.env$",
    r"\.env\.[^/]+$",
    r"secrets\.nix$",
    r"secrets/.*",
    r"credentials.*",
    r".*\.secret$",
    r"config\.json$",  # Often contains API keys
    r".*password.*",
]

# Patterns in content that suggest secrets
SECRET_CONTENT_PATTERNS = [
    r"(api[_-]?key|apikey)\s*[=:]\s*['\"][^'\"]+['\"]",
    r"(password|passwd|pwd)\s*[=:]\s*['\"][^'\"]+['\"]",
    r"(secret|token)\s*[=:]\s*['\"][^'\"]+['\"]",
    r"(aws_secret|aws_access)",
    r"-----BEGIN (RSA |OPENSSH |)PRIVATE KEY-----",
]


def check_file(file_path: str) -> tuple[bool, str | None]:
    """
    Check if file is sensitive.
    Returns: (should_block, message)
    """
    path = Path(file_path)
    name = path.name
    full_path = str(path)

    # Check blocked patterns
    for pattern in BLOCKED_FILES:
        if re.search(pattern, full_path, re.IGNORECASE):
            return True, f"BLOCKED: Editing {name} - this file contains sensitive credentials"

    # Check warning patterns
    for pattern in WARN_FILES:
        if re.search(pattern, full_path, re.IGNORECASE):
            return False, f"WARNING: Editing {name} - ensure no secrets are hardcoded. Use environment variables or agenix."

    return False, None


def check_content(content: str) -> str | None:
    """Check content for secret patterns."""
    for pattern in SECRET_CONTENT_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            return "WARNING: Content appears to contain secrets. Consider using environment variables instead."
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    content = tool_input.get("content", "") or tool_input.get("new_string", "")

    if not file_path:
        sys.exit(0)

    # Check file path
    should_block, message = check_file(file_path)

    if should_block:
        print(message, file=sys.stderr)
        sys.exit(2)

    # Check content for secrets
    content_warning = check_content(content) if content else None

    # Combine warnings
    warnings = [m for m in [message, content_warning] if m]

    if warnings:
        output = {
            "continue": True,
            "systemMessage": "\n".join(warnings)
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
