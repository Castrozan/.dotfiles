import json
import subprocess
from datetime import datetime, timezone

from run_evals_worktree_and_environment import REPO_ROOT

BASELINE_REPOSITORY_PATH = "agent-harness/quality/evaluations/baseline.json"
COMMIT_RECORD_PREFIX = "commit "
RESET_PLACEHOLDER_TOTAL_TESTS = 1


def baseline_evidence_age_days(
    baseline: dict, current_time: datetime | None = None
) -> int:
    evidence_timestamp = baseline.get("oldest_evidence_at", baseline["generated_at"])
    generated_at = datetime.fromisoformat(evidence_timestamp)
    now = current_time or datetime.now(timezone.utc)
    return (now - generated_at).days


def commits_touching_baseline():
    output = (
        subprocess.run(
            [
                "git",
                "log",
                "--follow",
                "--name-only",
                f"--format={COMMIT_RECORD_PREFIX}%H|%cI",
                "--",
                BASELINE_REPOSITORY_PATH,
            ],
            capture_output=True,
            text=True,
            check=True,
            cwd=REPO_ROOT,
        )
        .stdout.strip()
        .splitlines()
    )
    newest_first_records = []
    commit_sha = None
    committed_iso = None
    for line in output:
        if line.startswith(COMMIT_RECORD_PREFIX):
            commit_sha, committed_iso = line[len(COMMIT_RECORD_PREFIX) :].split("|", 1)
            continue
        if line.strip() and commit_sha is not None:
            newest_first_records.append((commit_sha, committed_iso, line.strip()))
            commit_sha = None
    yield from reversed(newest_first_records)


def baseline_at_commit(commit_sha, baseline_path_at_commit):
    blob = subprocess.run(
        ["git", "show", f"{commit_sha}:{baseline_path_at_commit}"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    ).stdout
    if not blob.strip():
        return None
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        return None


def committed_baseline_pass_rates(execution_profile):
    pass_rates = []
    for commit_sha, _, baseline_path_at_commit in commits_touching_baseline():
        baseline = baseline_at_commit(commit_sha, baseline_path_at_commit)
        if baseline is None:
            continue
        if baseline.get("total_tests") == RESET_PLACEHOLDER_TOTAL_TESTS:
            continue
        if baseline.get("execution_profile") != execution_profile:
            continue
        pass_rate = baseline.get("pass_rate")
        if isinstance(pass_rate, (int, float)):
            pass_rates.append(pass_rate)
    return pass_rates


def previous_committed_baseline_pass_rate(execution_profile) -> float | None:
    pass_rates = committed_baseline_pass_rates(execution_profile)
    if len(pass_rates) < 2:
        return None
    return pass_rates[-2]


def baseline_regression_failure(
    current_pass_rate: float, previous_pass_rate: float | None, maximum_drop: float
) -> str | None:
    if previous_pass_rate is None:
        return None
    drop = previous_pass_rate - current_pass_rate
    if drop > maximum_drop:
        return (
            f"Overall pass rate {current_pass_rate:.1%} dropped "
            f"{drop:.1%} below the previous baseline {previous_pass_rate:.1%} "
            f"(max allowed drop {maximum_drop:.1%})"
        )
    return None


def baseline_staleness_failure(age_days: int, maximum_age_days: int) -> str | None:
    if age_days <= maximum_age_days:
        return None
    return (
        f"Baseline is {age_days} days old, past the {maximum_age_days}-day "
        f"freshness window, so it no longer reflects the current instruction "
        f"surface; re-record it with 'agent-eval --save-baseline'"
    )
