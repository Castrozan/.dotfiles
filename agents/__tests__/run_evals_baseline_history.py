import json
import subprocess

from run_evals_worktree_and_environment import REPO_ROOT

BASELINE_REPOSITORY_PATH = "agents/evals/baseline.json"
RESET_PLACEHOLDER_TOTAL_TESTS = 1


def commits_touching_baseline():
    output = (
        subprocess.run(
            [
                "git",
                "log",
                "--reverse",
                "--format=%H|%cI",
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
    for line in output:
        commit_sha, committed_iso = line.split("|", 1)
        yield commit_sha, committed_iso


def baseline_at_commit(commit_sha):
    blob = subprocess.run(
        ["git", "show", f"{commit_sha}:{BASELINE_REPOSITORY_PATH}"],
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


def committed_baseline_pass_rates():
    pass_rates = []
    for commit_sha, _ in commits_touching_baseline():
        baseline = baseline_at_commit(commit_sha)
        if baseline is None:
            continue
        if baseline.get("total_tests") == RESET_PLACEHOLDER_TOTAL_TESTS:
            continue
        pass_rate = baseline.get("pass_rate")
        if isinstance(pass_rate, (int, float)):
            pass_rates.append(pass_rate)
    return pass_rates


def previous_committed_baseline_pass_rate() -> float | None:
    pass_rates = committed_baseline_pass_rates()
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
