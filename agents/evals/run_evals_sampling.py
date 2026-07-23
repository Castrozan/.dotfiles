from collections import defaultdict

from run_evals_statistics import pass_at_k, wilson_score_interval


def aggregate_repeated_runs(results_per_epoch):
    passes_by_test = defaultdict(int)
    totals_by_test = defaultdict(int)
    for epoch_results in results_per_epoch:
        for result in epoch_results:
            totals_by_test[result.name] += 1
            if result.passed:
                passes_by_test[result.name] += 1

    per_test = []
    for name in sorted(totals_by_test):
        passes = passes_by_test[name]
        total = totals_by_test[name]
        lower, upper = wilson_score_interval(passes, total)
        per_test.append(
            {
                "name": name,
                "passes": passes,
                "total": total,
                "lower": lower,
                "upper": upper,
                "flaky": 0 < passes < total,
            }
        )
    return per_test


def suite_pass_at_k(per_test, k):
    if not per_test:
        return 0.0
    return sum(pass_at_k(t["total"], t["passes"], k) for t in per_test) / len(per_test)
