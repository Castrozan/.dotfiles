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


def list_categories(config: dict) -> None:
    print("Available test categories:")
    for cat_name, tests in config.get("tests", {}).items():
        print(f"  {cat_name} ({len(tests)} tests)")
        for test in tests:
            print(f"    - {test['name']}")
    if config.get("smoke_test"):
        print("  smoke_test (1 test)")
        print(f"    - {config['smoke_test']['name']}")
