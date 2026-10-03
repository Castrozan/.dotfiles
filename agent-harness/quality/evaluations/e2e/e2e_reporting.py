from e2e.sessions.e2e_models import E2eScenarioResult
from e2e.sessions.e2e_trace import extract_tool_name_sequence


def print_e2e_results(
    results: list[E2eScenarioResult],
) -> bool:
    print("\n" + "=" * 60)
    print("E2E INTEGRATION TEST RESULTS (herdr tabs)")
    print("=" * 60 + "\n")

    all_passed = True

    for result in results:
        if not _print_e2e_result(result):
            all_passed = False

    _print_e2e_summary(results)

    return all_passed


def _print_e2e_result(result):
    status, color = _scenario_status_color(result.passed)
    score_color = _experience_score_color(result.experience_score)
    reset = "\033[0m"
    print(
        f"{color}{status}{reset} "
        f"{result.scenario_name} "
        f"({result.duration_seconds:.1f}s) "
        f"{score_color}NPS:{result.experience_score}"
        f"{reset}"
    )
    if result.error:
        print(f"    Error: {result.error}")
    for assertion in result.assertion_results:
        _print_assertion_result(assertion, reset)
    if not result.passed:
        _print_failed_tool_sequence(result)
    return result.passed


def _scenario_status_color(passed):
    if passed:
        return "✓", "\033[32m"
    return "✗", "\033[31m"


def _experience_score_color(score):
    if score >= 75:
        return "\033[32m"
    if score >= 50:
        return "\033[33m"
    return "\033[31m"


def _print_assertion_result(assertion, reset):
    symbol, color = _scenario_status_color(assertion.passed)
    print(f"    {color}{symbol}{reset} {assertion.name}: {assertion.detail}")


def _print_failed_tool_sequence(result):
    tool_sequence = extract_tool_name_sequence(result.trace)
    if tool_sequence:
        print(f"    Tools: {' -> '.join(tool_sequence)}")


def _print_e2e_summary(results):
    scored = [result for result in results if result.experience_score > 0]
    avg_score = (
        sum(result.experience_score for result in scored) / len(scored) if scored else 0
    )
    passed_count = sum(1 for result in results if result.passed)
    total_time = sum(result.duration_seconds for result in results)
    print(f"\n{'=' * 60}")
    print(f"Passed: {passed_count}/{len(results)}")
    print(f"Experience Score: {avg_score:.0f}/100")
    print(f"Total time: {total_time:.1f}s")
    print(f"{'=' * 60}\n")


def print_multi_run_pass_rate_summary(
    results: list[E2eScenarioResult],
    runs_per_scenario: int,
) -> None:
    grouped_results_by_scenario: dict[str, list[E2eScenarioResult]] = {}
    for result in results:
        grouped_results_by_scenario.setdefault(result.scenario_name, []).append(result)

    print(f"\n{'=' * 60}")
    print(f"MULTI-RUN PASS-RATE SUMMARY ({runs_per_scenario} runs per scenario)")
    print(f"{'=' * 60}\n")

    for scenario_name, scenario_runs in grouped_results_by_scenario.items():
        _print_scenario_pass_rate(scenario_name, scenario_runs)

    total_runs = len(results)
    total_passed = sum(1 for result in results if result.passed)
    print(f"\n  overall: {total_passed}/{total_runs}")
    print(f"{'=' * 60}\n")


def _print_scenario_pass_rate(scenario_name, scenario_runs):
    passed_runs = sum(1 for run in scenario_runs if run.passed)
    total_runs = len(scenario_runs)
    avg_nps = _average_experience_score(scenario_runs)
    print(f"  {scenario_name}: {passed_runs}/{total_runs} (NPS avg {avg_nps:.0f})")


def _average_experience_score(results):
    scored = [result for result in results if result.experience_score > 0]
    return (
        sum(result.experience_score for result in scored) / len(scored) if scored else 0
    )
