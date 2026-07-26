from run_evals_baseline_history import (
    RESET_PLACEHOLDER_TOTAL_TESTS,
    baseline_at_commit,
    commits_touching_baseline,
)


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
