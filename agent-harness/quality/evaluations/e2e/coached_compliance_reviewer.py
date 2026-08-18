import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coached_fixtures import build_coach_prompt  # noqa: E402
from run_evals_subject_binary import resolve_subject_claude_binary  # noqa: E402

COMPLIANCE_REVIEW_TIMEOUT_SECONDS = 60
NPS_PENALTY_PER_COMPLIANCE_FAILURE = 15


def review_tool_sequence_for_compliance(
    compliance_body: str, tool_sequence: list[str], workspace: Path
) -> str:
    completed = subprocess.run(
        [
            resolve_subject_claude_binary(),
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
