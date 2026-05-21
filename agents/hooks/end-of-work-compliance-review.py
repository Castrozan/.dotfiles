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

CORE_RULES_REINFORCEMENT = """CORE INSTRUCTION REINFORCEMENT:

These rules are non-negotiable. They were loaded via CLAUDE.md -> AGENTS.md
at session start but may have been lost during context compaction.

1. NO COMMENTS: Zero comments in code. Names replace comments. Long descriptive
   function and variable names are the documentation.
2. WORKFLOW SEQUENCE: After editing any file in the dotfiles repo:
   format -> git add specific-file -> commit -> /rebuild -> tests/run.sh
   Do not respond to the user until rebuild succeeds and tests pass.
3. INVESTIGATE BEFORE FIXING: When asked to analyze or debug, gather evidence
   first. Read real files. Do not guess from memory. Analysis and implementation
   are separate phases.
4. SPECIFIC STAGING: Always git add specific-file. Never git add -A or git add .
5. PYTHON OVER BASH: Python 3.12 is default for scripts. Bash only for thin
   shell-native wrappers.
6. TEST FIRST: When a bug is reported, write a failing test first. The passing
   test proves the fix.
7. ANTI-SYCOPHANCY: When challenged, re-read the code before agreeing or
   disagreeing. Do not tone-match.
8. GLOB OVER FIND: Use Glob tool for file search, Read tool for file reading.
   Do not use Bash for cat, grep, find when dedicated tools exist.
9. CONCISE COMMUNICATION: Be direct. No em dashes. No preamble.
"""


def load_compliance_skill_body() -> str:
    if not COMPLIANCE_SKILL_PATH.exists():
        return ""
    return COMPLIANCE_SKILL_PATH.read_text().strip()


def build_review_system_prompt() -> str:
    compliance_body = load_compliance_skill_body()
    if not compliance_body:
        return ""
    return f"{CORE_RULES_REINFORCEMENT}\n\n{compliance_body}"


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

    review_system_prompt = build_review_system_prompt()
    if not review_system_prompt:
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
                review_system_prompt,
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
