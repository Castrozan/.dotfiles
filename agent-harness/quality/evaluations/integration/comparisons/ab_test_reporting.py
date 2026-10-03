from integration.comparisons.ab_test_models import AbTestResult


def print_ab_test_results(
    all_results: list[AbTestResult],
    configurations: list[str],
) -> None:
    print("\n" + "=" * 70)
    print("INSTRUCTION LOADING A/B TEST - UNPROMPTED INSTRUCTION FOLLOWING")
    print("=" * 70)

    scenario_names = list(dict.fromkeys(result.scenario_name for result in all_results))

    header = f"{'Metric':<30}"
    for config_name in configurations:
        header += f" {config_name:>14}"
    print(f"\n{header}")
    print("-" * (30 + 15 * len(configurations)))

    for scenario_name in scenario_names:
        _print_scenario_metrics(scenario_name, all_results, configurations)

    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print("-" * 70)

    _print_configuration_summary(all_results, configurations)

    print(f"{'=' * 70}\n")


def _print_scenario_metrics(scenario_name, all_results, configurations):
    print(f"\n  Scenario: {scenario_name}")
    scenario_results = {
        result.configuration_name: result
        for result in all_results
        if result.scenario_name == scenario_name
    }
    metrics_to_display = [
        ("read_before_edit", "Read before edit"),
        ("used_glob_not_find", "Glob over find"),
        ("no_comments_in_written_code", "No comments in code"),
        ("used_descriptive_names", "Descriptive names"),
        ("used_specific_git_staging", "Specific git staging"),
        ("read_to_edit_ratio", "Read/edit ratio"),
        ("score", "SCORE"),
    ]
    for metric_key, metric_label in metrics_to_display:
        row = f"  {metric_label:<28}"
        for config_name in configurations:
            row = _append_metric_value(
                row, scenario_results.get(config_name), metric_key
            )
        print(row)


def _append_metric_value(row, result, metric_key):
    if not result:
        return f"{row} {'N/A':>14}"
    value = getattr(result.metrics, metric_key)
    if isinstance(value, bool):
        symbol = "\033[32mYES\033[0m" if value else "\033[31m NO\033[0m"
        return f"{row} {symbol:>23}"
    if isinstance(value, float):
        return f"{row} {value:>14.1f}"
    return f"{row} {value:>14}"


def _print_configuration_summary(all_results, configurations):
    for config_name in configurations:
        config_results = [
            result for result in all_results if result.configuration_name == config_name
        ]
        if not config_results:
            continue
        average_score = sum(result.metrics.score for result in config_results) / len(
            config_results
        )
        total_duration = sum(result.duration_seconds for result in config_results)
        print(
            f"  {config_name:<20} "
            f"avg score: {_score_color(average_score)}"
            f"{average_score:.0f}/100\033[0m  "
            f"time: {total_duration:.0f}s"
        )


def _score_color(average_score):
    if average_score >= 60:
        return "\033[32m"
    if average_score >= 40:
        return "\033[33m"
    return "\033[31m"
