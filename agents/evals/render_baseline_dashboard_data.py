import json
import subprocess

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
    ).stdout
    if not blob.strip():
        return None
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        return None


def collect_baseline_revisions():
    revisions = []
    for commit_sha, committed_iso in commits_touching_baseline():
        baseline = baseline_at_commit(commit_sha)
        if baseline is None:
            continue
        total_tests = baseline.get("total_tests")
        if total_tests == RESET_PLACEHOLDER_TOTAL_TESTS:
            continue
        rate = baseline.get("pass_rate")
        revisions.append(
            {
                "date": committed_iso[:10],
                "commit": commit_sha[:8],
                "passed": baseline.get("total_passed"),
                "total": total_tests,
                "rate": round(rate * 100, 1)
                if isinstance(rate, (int, float))
                else None,
            }
        )
    return revisions


def summarize_revisions(revisions):
    rated = [
        revision for revision in revisions if isinstance(revision["rate"], (int, float))
    ]
    if not rated:
        return None
    return {
        "latest": rated[-1],
        "peak": max(rated, key=lambda revision: revision["rate"]),
        "trough": min(rated, key=lambda revision: revision["rate"]),
        "count": len(rated),
        "first_date": rated[0]["date"],
        "last_date": rated[-1]["date"],
        "suite_min": min(revision["total"] for revision in rated),
        "suite_max": max(revision["total"] for revision in rated),
    }
