#!/usr/bin/env python3

import json
import os
import subprocess
import sys

FORMATTERS = {
    ".nix": {
        "formatters": [
            {"cmd": ["nixfmt"], "name": "nixfmt"},
        ],
        "timeout": 10,
    },
    ".py": {
        "formatters": [
            {"cmd": ["ruff", "format", "--quiet"], "name": "ruff"},
        ],
        "timeout": 10,
    },
    ".js": {
        "formatters": [
            {"cmd": ["prettier", "--write"], "name": "prettier"},
        ],
        "timeout": 10,
    },
    ".ts": {
        "formatters": [
            {"cmd": ["prettier", "--write"], "name": "prettier"},
        ],
        "timeout": 10,
    },
    ".tsx": {
        "formatters": [
            {"cmd": ["prettier", "--write"], "name": "prettier"},
        ],
        "timeout": 10,
    },
    ".jsx": {
        "formatters": [
            {"cmd": ["prettier", "--write"], "name": "prettier"},
        ],
        "timeout": 10,
    },
    ".json": {
        "formatters": [
            {"cmd": ["prettier", "--write"], "name": "prettier"},
            {"cmd": ["jq", ".", "--indent", "2"], "name": "jq", "redirect": True},
        ],
        "timeout": 5,
    },
    ".yaml": {
        "formatters": [
            {"cmd": ["prettier", "--write"], "name": "prettier"},
        ],
        "timeout": 5,
    },
    ".yml": {
        "formatters": [
            {"cmd": ["prettier", "--write"], "name": "prettier"},
        ],
        "timeout": 5,
    },
    ".sh": {
        "formatters": [
            {"cmd": ["shfmt", "-w"], "name": "shfmt"},
        ],
        "timeout": 5,
    },
    ".bash": {
        "formatters": [
            {"cmd": ["shfmt", "-w"], "name": "shfmt"},
        ],
        "timeout": 5,
    },
}


def check_formatter_available(formatter_cmd: list[str]) -> bool:
    try:
        subprocess.run([formatter_cmd[0], "--version"], capture_output=True, timeout=2)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        try:
            subprocess.run([formatter_cmd[0], "--help"], capture_output=True, timeout=2)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False


def run_formatter(file_path: str, formatter: dict) -> bool:
    cmd = formatter["cmd"] + [file_path]

    try:
        if formatter.get("redirect"):
            with open(file_path, "r") as f:
                content = f.read()

            result = subprocess.run(
                formatter["cmd"],
                input=content,
                text=True,
                capture_output=True,
                timeout=10,
            )

            if result.returncode == 0:
                with open(file_path, "w") as f:
                    f.write(result.stdout)
                return True
            return False
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0

    except (subprocess.TimeoutExpired, Exception):
        return False


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    file_path = data.get("tool_input", {}).get("file_path", "")

    if not file_path or not os.path.exists(file_path):
        sys.exit(0)

    try:
        if os.path.getsize(file_path) > 1024 * 1024:
            sys.exit(0)
    except OSError:
        sys.exit(0)

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext not in FORMATTERS:
        sys.exit(0)

    for formatter in FORMATTERS[ext]["formatters"]:
        if check_formatter_available(formatter["cmd"]):
            run_formatter(file_path, formatter)
            sys.exit(0)

    missing_names = [f["name"] for f in FORMATTERS[ext]["formatters"]]
    names = ", ".join(missing_names)
    message = f"No formatters for {ext} files. Install: {names}"
    print(json.dumps({"continue": True, "systemMessage": message}))
    sys.exit(0)


if __name__ == "__main__":
    main()
