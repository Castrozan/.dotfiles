#!/usr/bin/env python3
"""auto-format.py - Automatically format files after editing based on file type."""

import json
import os
import subprocess
import sys

# File type to formatter mapping
FORMATTERS = {
    ".nix": {
        "formatters": [
            {"cmd": ["nixfmt"], "name": "nixfmt"},
        ],
        "timeout": 10
    },
    ".py": {
        "formatters": [
            {"cmd": ["ruff", "format", "--quiet"], "name": "ruff"},
        ],
        "timeout": 10
    },
    ".js": {
        "formatters": [
            {"cmd": ["prettier", "--write"], "name": "prettier"},
        ],
        "timeout": 10
    },
    ".ts": {
        "formatters": [
            {"cmd": ["prettier", "--write"], "name": "prettier"},
        ],
        "timeout": 10
    },
    ".tsx": {
        "formatters": [
            {"cmd": ["prettier", "--write"], "name": "prettier"},
        ],
        "timeout": 10
    },
    ".jsx": {
        "formatters": [
            {"cmd": ["prettier", "--write"], "name": "prettier"},
        ],
        "timeout": 10
    },
    ".json": {
        "formatters": [
            {"cmd": ["prettier", "--write"], "name": "prettier"},
            {"cmd": ["jq", ".", "--indent", "2"], "name": "jq", "redirect": True},
        ],
        "timeout": 5
    },
    ".yaml": {
        "formatters": [
            {"cmd": ["prettier", "--write"], "name": "prettier"},
        ],
        "timeout": 5
    },
    ".yml": {
        "formatters": [
            {"cmd": ["prettier", "--write"], "name": "prettier"},
        ],
        "timeout": 5
    },
    ".sh": {
        "formatters": [
            {"cmd": ["shfmt", "-w"], "name": "shfmt"},
        ],
        "timeout": 5
    },
    ".bash": {
        "formatters": [
            {"cmd": ["shfmt", "-w"], "name": "shfmt"},
        ],
        "timeout": 5
    },
}

def check_formatter_available(formatter_cmd: list[str]) -> bool:
    """Check if a formatter is available in PATH."""
    try:
        subprocess.run(
            [formatter_cmd[0], "--version"],
            capture_output=True,
            timeout=2
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        try:
            # Some formatters don't support --version, try --help
            subprocess.run(
                [formatter_cmd[0], "--help"],
                capture_output=True,
                timeout=2
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

def format_file(file_path: str, formatter: dict) -> tuple[bool, str]:
    """Format a file with the given formatter."""
    cmd = formatter["cmd"] + [file_path]
    name = formatter["name"]

    try:
        if formatter.get("redirect"):
            # For formatters like jq that output to stdout
            with open(file_path, 'r') as f:
                content = f.read()

            result = subprocess.run(
                formatter["cmd"],
                input=content,
                text=True,
                capture_output=True,
                timeout=10
            )

            if result.returncode == 0:
                with open(file_path, 'w') as f:
                    f.write(result.stdout)
                return True, f"Formatted with {name}"
            else:
                return False, f"{name} failed: {result.stderr.strip()}"
        else:
            # For in-place formatters
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                return True, f"Formatted with {name}"
            else:
                return False, f"{name} failed: {result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        return False, f"{name} timed out"
    except Exception as e:
        return False, f"{name} error: {str(e)}"

def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    file_path = data.get("tool_input", {}).get("file_path", "")

    if not file_path or not os.path.exists(file_path):
        sys.exit(0)

    # Skip if file is too large (> 1MB)
    try:
        file_size = os.path.getsize(file_path)
        if file_size > 1024 * 1024:  # 1MB
            sys.exit(0)
    except OSError:
        sys.exit(0)

    # Get file extension
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext not in FORMATTERS:
        sys.exit(0)

    config = FORMATTERS[ext]
    messages = []

    # Try formatters in order of preference
    for formatter in config["formatters"]:
        if not check_formatter_available(formatter["cmd"]):
            continue

        success, message = format_file(file_path, formatter)
        if success:
            messages.append(f"✨ {message}")
            break
        else:
            # Don't show error messages unless no formatter worked
            continue

    if not messages:
        # No formatter available or all failed
        formatter_names = [f["name"] for f in config["formatters"]]
        messages.append(f"⚠️  No formatters available for {ext} files. Consider installing: {', '.join(formatter_names)}")

    if messages:
        output = {
            "continue": True,
            "systemMessage": "\n".join(messages)
        }
        print(json.dumps(output))

    sys.exit(0)

if __name__ == "__main__":
    main()