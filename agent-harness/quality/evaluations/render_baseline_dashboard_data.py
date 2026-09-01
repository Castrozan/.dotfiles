from run_evals_baseline_history import (
    RESET_PLACEHOLDER_TOTAL_TESTS,
    baseline_at_commit,
    commits_touching_baseline,
)


USAGE_TOTAL_FIELDS = (
    "invocations",
    "measured_invocations",
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)


def summarize_token_usage(token_usage):
    totals = {field: 0 for field in USAGE_TOTAL_FIELDS}
    for harnesses in token_usage.values():
        for usage in harnesses.values():
            for field in USAGE_TOTAL_FIELDS:
                totals[field] += usage.get(field, 0)
    return totals


def collect_baseline_revisions():
    revisions = []
    for (
        commit_sha,
        committed_iso,
        baseline_path_at_commit,
    ) in commits_touching_baseline():
        baseline = baseline_at_commit(commit_sha, baseline_path_at_commit)
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
                "usage": summarize_token_usage(baseline.get("token_usage", {})),
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
