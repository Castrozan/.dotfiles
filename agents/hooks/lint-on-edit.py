#!/usr/bin/env python3
"""lint-on-edit.py - Run linters after file edits and report issues."""

import json
import os
import subprocess
import sys


# File type to linter mapping
LINTERS = {
    ".py": [
        {
            "cmd": ["ruff", "check", "--select=E,F,W"],
            "name": "ruff",
            "parse": lambda out: [l for l in out.split("\n") if l.strip() and not l.startswith("Found")]
        },
        {
            "cmd": ["flake8", "--select=E,F,W"],
            "name": "flake8",
            "parse": lambda out: out.strip().split("\n") if out.strip() else []
        },
        {
            "cmd": ["mypy", "--no-error-summary"],
            "name": "mypy",
            "parse": lambda out: [l for l in out.split("\n") if ": error:" in l or ": warning:" in l]
        },
    ],
    ".js": [
        {
            "cmd": ["eslint", "--format=compact"],
            "name": "eslint",
            "parse": lambda out: [l for l in out.split("\n") if "Error" in l or "Warning" in l][:5]
        },
    ],
    ".ts": [
        {
            "cmd": ["eslint", "--format=compact"],
            "name": "eslint",
            "parse": lambda out: [l for l in out.split("\n") if "Error" in l or "Warning" in l][:5]
        },
        {
            "cmd": ["tsc", "--noEmit"],
            "name": "tsc",
            "parse": lambda out: [l for l in out.split("\n") if "error TS" in l][:5]
        },
    ],
    ".tsx": [
        {
            "cmd": ["eslint", "--format=compact"],
            "name": "eslint",
            "parse": lambda out: [l for l in out.split("\n") if "Error" in l or "Warning" in l][:5]
        },
    ],
    ".nix": [
        {
            "cmd": ["statix", "check"],
            "name": "statix",
            "parse": lambda out: [l for l in out.split("\n") if ">" in l or "Warning" in l][:5]
        },
        {
            "cmd": ["deadnix"],
            "name": "deadnix",
            "parse": lambda out: [l for l in out.split("\n") if l.strip()][:5]
        },
    ],
    ".sh": [
        {
            "cmd": ["shellcheck", "--format=gcc"],
            "name": "shellcheck",
            "parse": lambda out: [l for l in out.split("\n") if "error:" in l.lower() or "warning:" in l.lower()][:5]
        },
    ],
    ".rs": [
        {
            "cmd": ["cargo", "clippy", "--message-format=short", "-q"],
            "name": "clippy",
            "parse": lambda out: [l for l in out.split("\n") if "warning:" in l or "error:" in l][:5]
        },
    ],
    ".go": [
        {
            "cmd": ["go", "vet"],
            "name": "go vet",
            "parse": lambda out: out.strip().split("\n")[:5] if out.strip() else []
        },
        {
            "cmd": ["staticcheck"],
            "name": "staticcheck",
            "parse": lambda out: out.strip().split("\n")[:5] if out.strip() else []
        },
    ],
}


def check_linter_available(linter_cmd: list[str]) -> bool:
    """Check if a linter is available in PATH."""
    try:
        subprocess.run(
            [linter_cmd[0], "--version"],
            capture_output=True,
            timeout=2
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        try:
            subprocess.run(
                [linter_cmd[0], "--help"],
                capture_output=True,
                timeout=2
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False


def run_linter(file_path: str, linter: dict) -> list[str]:
    """Run a linter and return issues found."""
    cmd = linter["cmd"] + [file_path]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.path.dirname(file_path) or "."
        )
        # Linters often return non-zero when issues found
        output = result.stdout + result.stderr
        issues = linter["parse"](output)
        return [issue for issue in issues if issue.strip()]
    except subprocess.TimeoutExpired:
        return []
    except Exception:
        return []


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    file_path = data.get("tool_input", {}).get("file_path", "")

    if not file_path or not os.path.exists(file_path):
        sys.exit(0)

    # Get file extension
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext not in LINTERS:
        sys.exit(0)

    # Skip if file is too large (> 500KB)
    try:
        if os.path.getsize(file_path) > 500 * 1024:
            sys.exit(0)
    except OSError:
        sys.exit(0)

    all_issues = []
    linters_run = []

    for linter in LINTERS[ext]:
        if not check_linter_available(linter["cmd"]):
            continue

        linters_run.append(linter["name"])
        issues = run_linter(file_path, linter)
        if issues:
            all_issues.extend(issues[:3])  # Limit per linter
            break  # Stop after first linter with issues

    if not linters_run:
        # No linters available
        sys.exit(0)

    if all_issues:
        # Truncate and format issues
        display_issues = all_issues[:5]
        issue_text = "\n".join(f"  - {issue}" for issue in display_issues)
        if len(all_issues) > 5:
            issue_text += f"\n  ... and {len(all_issues) - 5} more"

        output = {
            "continue": True,
            "systemMessage": f"LINT ISSUES ({linters_run[0]}):\n{issue_text}"
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
