from run_evals_sampling import suite_pass_at_k
from run_evals_statistics import format_pass_rate_with_confidence_interval
from run_evals_test_runner import TestResult


def print_results(results: list[TestResult]) -> bool:
    print("\n" + "=" * 60)
    print("AGENT EVALUATION RESULTS (Claude Max/CLI)")
    print("=" * 60 + "\n")

    passed = 0
    failed = 0
    total_duration = 0.0

    for result in results:
        total_duration += result.duration
        status = "✓" if result.passed else "✗"
        color = "\033[32m" if result.passed else "\033[31m"
        reset = "\033[0m"

        print(f"{color}{status}{reset} {result.name} ({result.duration:.1f}s)")

        if result.error:
            print(f"    Error: {result.error}")
        elif result.assertions_failed:
            for failure in result.assertions_failed:
                print(f"    - {failure}")

        if result.passed:
            passed += 1
        else:
            failed += 1

    print("\n" + "-" * 60)
    print(f"Passed: {passed}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")
    print(format_pass_rate_with_confidence_interval(passed, len(results)))
    print(f"Total time: {total_duration:.1f}s")
    print("-" * 60 + "\n")

    return failed == 0


def print_epoch_summary(per_test: list[dict], epochs: int) -> bool:
    print("\n" + "=" * 60)
    print(f"REPEATED-SAMPLING SUMMARY ({epochs} epochs)")
    print("=" * 60 + "\n")

    flaky_tests = [test for test in per_test if test["flaky"]]
    hard_failed_tests = [test for test in per_test if test["passes"] == 0]

    for test in per_test:
        rate = test["passes"] / test["total"] if test["total"] else 0.0
        marker = "FLAKY" if test["flaky"] else ("FAIL" if test["passes"] == 0 else "ok")
        print(
            f"  [{marker}] {test['name']}: {test['passes']}/{test['total']} "
            f"({rate:.0%}, 95% CI {test['lower']:.0%} to {test['upper']:.0%})"
        )

    print(f"\n  suite pass@1: {suite_pass_at_k(per_test, 1):.1%}")
    if epochs >= 2:
        print(f"  suite pass@2: {suite_pass_at_k(per_test, 2):.1%}")
    print(f"  flaky: {len(flaky_tests)}   hard-failed: {len(hard_failed_tests)}")
    print("-" * 60 + "\n")

    return len(hard_failed_tests) == 0


def print_ab_summary(comparison: dict) -> bool:
    print("\n" + "=" * 60)
    print("A/B INSTRUCTION-LOADING EXPERIMENT")
    print("=" * 60 + "\n")

    print(f"  Paired tests: {comparison['n_paired']}")
    print(
        f"  With instructions:    {comparison['variant_a_pass_rate']:.1%} "
        f"({comparison['both_pass'] + comparison['a_only_wins']}/{comparison['n_paired']})"
    )
    print(
        f"  Without instructions: {comparison['variant_b_pass_rate']:.1%} "
        f"({comparison['both_pass'] + comparison['b_only_wins']}/{comparison['n_paired']})"
    )
    print(f"  Delta: {comparison['delta']:+.1%}")
    print(
        f"  Discordant: instructions-only won {comparison['a_only_wins']}, "
        f"control-only won {comparison['b_only_wins']}"
    )
    print(
        f"  McNemar exact p = {comparison['p_value']:.4f} "
        f"({'significant' if comparison['significant'] else 'not significant'} at 0.05)"
    )
    print("-" * 60 + "\n")

    return comparison["significant"] and comparison["delta"] > 0


def print_calibration_summary(agreement: dict) -> bool:
    print("\n" + "=" * 60)
    print("JUDGE CALIBRATION")
    print("=" * 60 + "\n")

    print(f"  Cases: {agreement['n']}")
    print(
        f"  Agreement: {agreement['agreements']}/{agreement['n']} "
        f"({agreement['accuracy']:.1%})"
    )
    print(f"  Cohen's kappa: {agreement['cohens_kappa']:.3f}")
    if agreement["disagreements"]:
        print("  Disagreements:")
        for disagreement in agreement["disagreements"]:
            human = "PASS" if disagreement["human"] else "FAIL"
            judged = "PASS" if disagreement["judge"] else "FAIL"
            print(
                f"    - {disagreement['name']}: "
                f"human={human} judge={judged} ({disagreement['reason']})"
            )
    print("-" * 60 + "\n")

    return agreement["accuracy"] >= 0.8


def list_categories(config: dict) -> None:
    print("Available test categories:")
    for cat_name, tests in config.get("tests", {}).items():
        print(f"  {cat_name} ({len(tests)} tests)")
        for test in tests:
            print(f"    - {test['name']}")
    if config.get("smoke_test"):
        print("  smoke_test (1 test)")
        print(f"    - {config['smoke_test']['name']}")
