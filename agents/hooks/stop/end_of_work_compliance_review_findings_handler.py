"""Parse haiku review output and emit the block-or-pass decision to stdout."""

import json

from end_of_work_compliance_review_logging import log_status


def parse_fail_lines_from_haiku_output(review_stdout: str) -> list[str]:
    return [
        line.strip()
        for line in review_stdout.split("\n")
        if line.strip().startswith("FAIL:")
    ]


def build_block_decision_from_fail_lines(fail_lines: list[str]) -> dict:
    feedback = "COMPLIANCE REVIEW FAILED. Fix these before responding:\n" + "\n".join(
        fail_lines
    )
    return {"decision": "block", "reason": feedback}


def emit_review_decision_to_stdout(review_stdout: str, elapsed_seconds: int) -> None:
    fail_lines = parse_fail_lines_from_haiku_output(review_stdout.strip())

    if not fail_lines:
        log_status(
            f"haiku returned in {elapsed_seconds}s, no FAIL lines, turn proceeds"
        )
        return

    log_status(
        f"haiku returned in {elapsed_seconds}s, {len(fail_lines)} FAIL line(s), "
        f"blocking turn"
    )
    for fail_line in fail_lines:
        log_status(f"  {fail_line}")

    print(json.dumps(build_block_decision_from_fail_lines(fail_lines)))
