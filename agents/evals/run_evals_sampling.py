from collections import defaultdict

from run_evals_statistics import pass_at_k, wilson_score_interval


def aggregate_repeated_runs(results_per_epoch):
    passes_by_test = defaultdict(int)
    totals_by_test = defaultdict(int)
    category_by_test = {}
    for epoch_results in results_per_epoch:
        for result in epoch_results:
            totals_by_test[result.name] += 1
            category_by_test.setdefault(result.name, result.category)
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
                "category": category_by_test[name],
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


def build_epoch_enriched_baseline(per_test, epochs, git_commit, generated_at):
    categories = {}
    total_samples = 0
    total_sample_passes = 0
    for test in per_test:
        bucket = categories.setdefault(
            test["category"], {"passed": 0, "failed": 0, "tests": []}
        )
        majority_passed = test["passes"] * 2 >= test["total"]
        bucket["tests"].append(
            {
                "name": test["name"],
                "passed": majority_passed,
                "passes": test["passes"],
                "samples": test["total"],
                "lower": round(test["lower"], 4),
                "upper": round(test["upper"], 4),
            }
        )
        bucket["passed" if majority_passed else "failed"] += 1
        total_samples += test["total"]
        total_sample_passes += test["passes"]

    total_tests = len(per_test)
    total_passed = sum(bucket["passed"] for bucket in categories.values())
    return {
        "generated_at": generated_at,
        "git_commit": git_commit,
        "total_tests": total_tests,
        "total_passed": total_passed,
        "total_failed": total_tests - total_passed,
        "pass_rate": round(total_passed / total_tests, 4) if total_tests else 0,
        "categories": dict(sorted(categories.items())),
        "sampling": {
            "epochs": epochs,
            "total_samples": total_samples,
            "sample_pass_rate": (
                round(total_sample_passes / total_samples, 4) if total_samples else 0
            ),
            "suite_pass_at_1": round(suite_pass_at_k(per_test, 1), 4),
            "suite_pass_at_2": (
                round(suite_pass_at_k(per_test, 2), 4) if epochs >= 2 else None
            ),
            "flaky_tests": [test["name"] for test in per_test if test["flaky"]],
        },
    }
