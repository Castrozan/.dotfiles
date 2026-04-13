#!/usr/bin/env python3

import json
import os
import subprocess
import sys
from pathlib import Path

COMPLIANCE_SKILL_PATH = (
    Path.home() / ".dotfiles" / "agents" / "skills" / "review" / "compliance.md"
)

MINIMUM_TOOL_COUNT_FOR_REVIEW = 2


def load_compliance_skill_body() -> str:
    if not COMPLIANCE_SKILL_PATH.exists():
        return ""
    return COMPLIANCE_SKILL_PATH.read_text().strip()


def extract_tool_sequence_from_message(
    last_message: str,
) -> list[str]:
    tool_indicators = [
        "Read",
        "Edit",
        "Write",
        "Bash",
        "Glob",
        "Grep",
        "Update",
    ]
    found_tools = []
    for indicator in tool_indicators:
        if indicator in last_message:
            found_tools.append(indicator)
    return found_tools


def get_recent_git_diff() -> str:
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD~1", "--stat"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            full_diff = subprocess.run(
                ["git", "diff", "HEAD~1"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return full_diff.stdout[:2000]
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["git", "diff", "--cached"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.stdout.strip():
            return result.stdout[:2000]
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["git", "diff"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout[:2000]
    except Exception:
        return ""


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    last_message = data.get("last_assistant_message", "")
    if not last_message:
        sys.exit(0)

    tool_sequence = extract_tool_sequence_from_message(last_message)
    if len(tool_sequence) < MINIMUM_TOOL_COUNT_FOR_REVIEW:
        sys.exit(0)

    has_edit_or_write = any(
        tool in tool_sequence for tool in ("Edit", "Write", "Update")
    )
    if not has_edit_or_write:
        sys.exit(0)

    git_diff = get_recent_git_diff()
    if not git_diff:
        sys.exit(0)

    compliance_body = load_compliance_skill_body()
    if not compliance_body:
        sys.exit(0)

    tool_list = ", ".join(tool_sequence)
    review_prompt = (
        f"Tool sequence: {tool_list}\n\n"
        f"Git diff:\n```\n{git_diff}\n```\n\n"
        "Check each rule. Report PASS/FAIL/UNKNOWN."
    )

    try:
        review_result = subprocess.run(
            [
                "claude",
                "-p",
                "--model",
                "haiku",
                "--system-prompt",
                compliance_body,
                review_prompt,
            ],
            capture_output=True,
            text=True,
            timeout=30,
            env={
                key: value for key, value in os.environ.items() if key != "CLAUDECODE"
            },
        )
        findings = review_result.stdout.strip()
    except Exception:
        sys.exit(0)

    if "FAIL:" not in findings:
        sys.exit(0)

    fail_lines = [
        line.strip()
        for line in findings.split("\n")
        if line.strip().startswith("FAIL:")
    ]
    feedback = "COMPLIANCE REVIEW FAILED. Fix these before responding:\n" + "\n".join(
        fail_lines
    )

    output = {"decision": "block", "reason": feedback}
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
