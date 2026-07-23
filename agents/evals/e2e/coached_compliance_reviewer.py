import subprocess
from pathlib import Path

from coached_fixtures import build_coach_prompt

COMPLIANCE_REVIEW_TIMEOUT_SECONDS = 60
NPS_PENALTY_PER_COMPLIANCE_FAILURE = 15


def review_tool_sequence_for_compliance(
    compliance_body: str, tool_sequence: list[str], workspace: Path
) -> str:
    completed = subprocess.run(
        [
            "claude",
            "-p",
            "--model",
            "haiku",
            "--system-prompt",
            compliance_body,
            build_coach_prompt(tool_sequence, workspace),
        ],
        capture_output=True,
        text=True,
        timeout=COMPLIANCE_REVIEW_TIMEOUT_SECONDS,
        cwd=workspace,
    )
    return completed.stdout.strip()


def count_compliance_failures(findings: str) -> int:
    return findings.count("FAIL:")


def nps_after_compliance_penalty(nps: int, failure_count: int) -> int:
    return max(0, nps - (failure_count * NPS_PENALTY_PER_COMPLIANCE_FAILURE))
