from integration_models import ScenarioResult
from integration_session import extract_tool_name_sequence


def print_scenario_results(
    results: list[ScenarioResult],
) -> bool:
    print("\n" + "=" * 60)
    print("INTEGRATION TEST RESULTS")
    print("=" * 60 + "\n")

    all_passed = True

    for result in results:
        _print_scenario_details(result)

        if not result.passed:
            all_passed = False
            _print_failure_tool_sequence(result)

    passed_count = sum(1 for result in results if result.passed)
    scored_results = [result for result in results if result.experience_score > 0]
    _print_scenario_summary(results, passed_count, scored_results)

    return all_passed


def _print_scenario_details(result):
    status_symbol = "✓" if result.passed else "✗"
    color = "\033[32m" if result.passed else "\033[31m"
    reset = "\033[0m"
    print(
        f"{color}{status_symbol}{reset} "
        f"{result.scenario_name} "
        f"({result.duration_seconds:.1f}s) "
        f"{_experience_score_color(result.experience_score)}NPS:{result.experience_score}"
        f"{reset}"
    )
    if result.error:
        print(f"    Error: {result.error}")
    for assertion_result in result.assertion_results:
        _print_assertion_result(assertion_result)


def _experience_score_color(score):
    if score >= 75:
        return "\033[32m"
    if score >= 50:
        return "\033[33m"
    return "\033[31m"


def _print_assertion_result(assertion_result):
    assertion_symbol = "✓" if assertion_result.passed else "✗"
    assertion_color = "\033[32m" if assertion_result.passed else "\033[31m"
    print(
        f"    {assertion_color}{assertion_symbol}"
        f"\033[0m "
        f"{assertion_result.name}: "
        f"{assertion_result.detail}"
    )


def _print_failure_tool_sequence(result):
    tool_sequence = extract_tool_name_sequence(result.trace)
    if tool_sequence:
        print(f"    Tool sequence: {' -> '.join(tool_sequence)}")


def _print_scenario_summary(results, passed_count, scored_results):
    average_experience_score = (
        sum(result.experience_score for result in scored_results) / len(scored_results)
        if scored_results
        else 0
    )
    total_duration = sum(result.duration_seconds for result in results)
    print(f"\n{'=' * 60}")
    print(f"Passed: {passed_count}/{len(results)}")
    print(f"Experience Score: {average_experience_score:.0f}/100")
    print(f"Total time: {total_duration:.1f}s")
    print(f"{'=' * 60}\n")
