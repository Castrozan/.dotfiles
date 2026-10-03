from e2e.coaching.coached_models import CoachedSessionResult


def print_coached_results(results: list[CoachedSessionResult]) -> None:
    print("\n" + "=" * 70)
    print("COACHED SESSION RESULTS (worker + compliance coach)")
    print("=" * 70 + "\n")

    for result in results:
        _print_coached_result(result)

    initial_avg = (
        sum(result.initial_nps for result in results) / len(results) if results else 0
    )
    coached_avg = (
        sum(result.coached_nps for result in results) / len(results) if results else 0
    )
    improvement_avg = coached_avg - initial_avg

    print(f"{'=' * 70}")
    print(
        f"  Initial: {initial_avg:.0f}  ->  "
        f"Coached: {coached_avg:.0f}  "
        f"({improvement_avg:+.0f})"
    )
    print(f"{'=' * 70}\n")


def _print_coached_result(result):
    improvement_color = _improvement_color(result.improvement)
    reset = "\033[0m"
    initial_color = _nps_color(result.initial_nps)
    coached_color = _nps_color(result.coached_nps)
    print(f"  {result.scenario_name} ({result.duration_seconds:.0f}s)")
    print(
        f"    Initial: {initial_color}NPS {result.initial_nps}{reset}"
        f"  ->  Coached: {coached_color}NPS {result.coached_nps}{reset}"
        f"  ({improvement_color}{result.improvement:+d}{reset})"
    )
    if result.error:
        print(f"    Error: {result.error}")
    if result.coach_findings:
        _print_coach_findings(result.coach_findings)
    print()


def _print_coach_findings(coach_findings):
    for line in coach_findings.split("\n"):
        stripped = line.strip()
        if stripped.startswith("FAIL:"):
            print(f"    \033[31m{stripped}\033[0m")
        elif stripped.startswith("PASS:"):
            print(f"    \033[32m{stripped}\033[0m")


def _improvement_color(improvement):
    if improvement > 0:
        return "\033[32m"
    if improvement == 0:
        return "\033[33m"
    return "\033[31m"


def _nps_color(nps):
    if nps >= 75:
        return "\033[32m"
    if nps >= 50:
        return "\033[33m"
    return "\033[31m"
