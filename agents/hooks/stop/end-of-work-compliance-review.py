#!/usr/bin/env python3

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from end_of_work_compliance_review_logging import (  # noqa: E402, F401
    SINGLE_INSTANCE_LOCK_FILE_PATH,
    acquire_single_instance_lock_or_none,
    get_session_id_short_prefix,
    log_status,
    set_session_id_short_prefix,
)
from end_of_work_compliance_review_prompt_builder import (  # noqa: E402, F401
    MAX_TOOL_CALLS_IN_PROMPT,
    build_review_user_prompt,
    summarize_tool_call_for_prompt,
)
from end_of_work_compliance_review_subprocess import (  # noqa: E402
    run_review_subprocess_with_liveness_polling,
)
from end_of_work_compliance_review_transcript_parser import (  # noqa: E402
    extract_current_turn_context_from_transcript,
    has_any_file_mutating_tool_call,
)
from end_of_work_compliance_review_workspace import (  # noqa: E402, F401
    COMPLIANCE_SKILL_PATH,
    MAX_WORKSPACE_DOC_CHARS,
    get_recent_git_diff,
    load_compliance_skill_body,
    load_workspace_policy_docs,
)

MINIMUM_TOOL_COUNT_FOR_REVIEW = 2


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        log_status("skipped: stdin was not valid JSON")
        sys.exit(0)

    set_session_id_short_prefix(data.get("session_id", ""))

    transcript_path_string = data.get("transcript_path", "")
    if not transcript_path_string:
        log_status("skipped: no transcript_path in Stop payload")
        sys.exit(0)

    transcript_path = Path(transcript_path_string)
    current_turn_context = extract_current_turn_context_from_transcript(transcript_path)
    if not current_turn_context:
        log_status(f"skipped: could not extract turn context from {transcript_path}")
        sys.exit(0)

    ordered_tool_calls = current_turn_context.get("ordered_tool_calls", [])
    if len(ordered_tool_calls) < MINIMUM_TOOL_COUNT_FOR_REVIEW:
        log_status(
            f"skipped: only {len(ordered_tool_calls)} tool call(s) this turn, "
            f"need at least {MINIMUM_TOOL_COUNT_FOR_REVIEW}"
        )
        sys.exit(0)

    if not has_any_file_mutating_tool_call(ordered_tool_calls):
        tool_names_summary = ", ".join(
            tool_call.get("name", "?") for tool_call in ordered_tool_calls[:10]
        )
        log_status(f"skipped: read-only turn (tools: {tool_names_summary})")
        sys.exit(0)

    workspace_cwd = current_turn_context.get("workspace_cwd") or os.getcwd()
    session_start_timestamp = current_turn_context.get("session_start_timestamp", "")
    git_diff = get_recent_git_diff(workspace_cwd, session_start_timestamp)
    if not git_diff:
        log_status("skipped: no git diff available to review")
        sys.exit(0)

    compliance_body = load_compliance_skill_body()
    if not compliance_body:
        log_status(
            f"skipped: compliance skill missing or empty at {COMPLIANCE_SKILL_PATH}"
        )
        sys.exit(0)

    workspace_policy_docs = load_workspace_policy_docs(workspace_cwd)

    review_user_prompt = build_review_user_prompt(
        current_turn_context, workspace_policy_docs, git_diff
    )

    single_instance_lock_handle = acquire_single_instance_lock_or_none()
    if single_instance_lock_handle is None:
        log_status(
            "skipped: another instance is already running "
            f"(lock at {SINGLE_INSTANCE_LOCK_FILE_PATH})"
        )
        sys.exit(0)

    tool_name_summary = ", ".join(
        tool_call.get("name", "?") for tool_call in ordered_tool_calls[:8]
    )
    log_status(
        f"starting haiku review (tools: {tool_name_summary}; "
        f"diff: {len(git_diff)} chars; rules: {len(compliance_body)} chars; "
        f"prompt: {len(review_user_prompt)} chars; "
        f"docs: {', '.join(workspace_policy_docs.keys()) or 'none'})"
    )

    subprocess_environment = {
        key: value for key, value in os.environ.items() if key != "CLAUDECODE"
    }
    review_command = [
        "claude",
        "-p",
        "--model",
        "haiku",
        "--system-prompt",
        compliance_body,
        review_user_prompt,
    ]

    review_start_timestamp = time.monotonic()

    try:
        review_stdout = run_review_subprocess_with_liveness_polling(
            review_command, subprocess_environment
        )
    except Exception as unexpected_review_failure:
        elapsed_seconds = int(time.monotonic() - review_start_timestamp)
        log_status(
            f"haiku subprocess failed after {elapsed_seconds}s: "
            f"{type(unexpected_review_failure).__name__}: "
            f"{unexpected_review_failure}"
        )
        sys.exit(0)

    elapsed_seconds = int(time.monotonic() - review_start_timestamp)

    if review_stdout is None:
        log_status(
            f"no review output after {elapsed_seconds}s (subprocess killed or empty)"
        )
        sys.exit(0)

    findings = review_stdout.strip()

    fail_lines = [
        line.strip()
        for line in findings.split("\n")
        if line.strip().startswith("FAIL:")
    ]

    if not fail_lines:
        log_status(
            f"haiku returned in {elapsed_seconds}s, no FAIL lines, turn proceeds"
        )
        sys.exit(0)

    log_status(
        f"haiku returned in {elapsed_seconds}s, {len(fail_lines)} FAIL line(s), "
        f"blocking turn"
    )
    for fail_line in fail_lines:
        log_status(f"  {fail_line}")

    feedback = "COMPLIANCE REVIEW FAILED. Fix these before responding:\n" + "\n".join(
        fail_lines
    )

    output = {"decision": "block", "reason": feedback}
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
