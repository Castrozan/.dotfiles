from e2e_models import E2eScenarioResult
from e2e_trace import extract_tool_name_sequence


def print_e2e_results(
    results: list[E2eScenarioResult],
) -> bool:
    print("\n" + "=" * 60)
    print("E2E INTEGRATION TEST RESULTS (tmux sessions)")
    print("=" * 60 + "\n")

    all_passed = True

    for result in results:
        status = "✓" if result.passed else "✗"
        color = "\033[32m" if result.passed else "\033[31m"
        score_color = (
            "\033[32m"
            if result.experience_score >= 75
            else "\033[33m"
            if result.experience_score >= 50
            else "\033[31m"
        )
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

        for a in result.assertion_results:
            a_sym = "✓" if a.passed else "✗"
            a_col = "\033[32m" if a.passed else "\033[31m"
            print(f"    {a_col}{a_sym}{reset} {a.name}: {a.detail}")

        if not result.passed:
            all_passed = False
            tool_seq = extract_tool_name_sequence(result.trace)
            if tool_seq:
                print(f"    Tools: {' -> '.join(tool_seq)}")

    scored = [r for r in results if r.experience_score > 0]
    avg_score = sum(r.experience_score for r in scored) / len(scored) if scored else 0
    passed_count = sum(1 for r in results if r.passed)
    total_time = sum(r.duration_seconds for r in results)

    print(f"\n{'=' * 60}")
    print(f"Passed: {passed_count}/{len(results)}")
    print(f"Experience Score: {avg_score:.0f}/100")
    print(f"Total time: {total_time:.1f}s")
    print(f"{'=' * 60}\n")

    return all_passed


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
        passed_runs = sum(1 for r in scenario_runs if r.passed)
        total_runs = len(scenario_runs)
        scored_runs = [r for r in scenario_runs if r.experience_score > 0]
        avg_nps = (
            sum(r.experience_score for r in scored_runs) / len(scored_runs)
            if scored_runs
            else 0
        )
        print(f"  {scenario_name}: {passed_runs}/{total_runs} (NPS avg {avg_nps:.0f})")

    total_runs = len(results)
    total_passed = sum(1 for r in results if r.passed)
    print(f"\n  overall: {total_passed}/{total_runs}")
    print(f"{'=' * 60}\n")
