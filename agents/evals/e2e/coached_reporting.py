from coached_models import CoachedSessionResult


def print_coached_results(results: list[CoachedSessionResult]) -> None:
    print("\n" + "=" * 70)
    print("COACHED SESSION RESULTS (worker + compliance coach)")
    print("=" * 70 + "\n")

    for result in results:
        improvement_color = (
            "\033[32m"
            if result.improvement > 0
            else "\033[33m"
            if result.improvement == 0
            else "\033[31m"
        )
        reset = "\033[0m"

        initial_color = (
            "\033[32m"
            if result.initial_nps >= 75
            else "\033[33m"
            if result.initial_nps >= 50
            else "\033[31m"
        )
        coached_color = (
            "\033[32m"
            if result.coached_nps >= 75
            else "\033[33m"
            if result.coached_nps >= 50
            else "\033[31m"
        )

        print(f"  {result.scenario_name} ({result.duration_seconds:.0f}s)")
        print(
            f"    Initial: {initial_color}NPS {result.initial_nps}{reset}"
            f"  ->  Coached: {coached_color}NPS {result.coached_nps}{reset}"
            f"  ({improvement_color}{result.improvement:+d}{reset})"
        )

        if result.error:
            print(f"    Error: {result.error}")

        if result.coach_findings:
            for line in result.coach_findings.split("\n"):
                stripped = line.strip()
                if stripped.startswith("FAIL:"):
                    print(f"    \033[31m{stripped}\033[0m")
                elif stripped.startswith("PASS:"):
                    print(f"    \033[32m{stripped}\033[0m")

        print()

    initial_avg = sum(r.initial_nps for r in results) / len(results) if results else 0
    coached_avg = sum(r.coached_nps for r in results) / len(results) if results else 0
    improvement_avg = coached_avg - initial_avg

    print(f"{'=' * 70}")
    print(
        f"  Initial: {initial_avg:.0f}  ->  "
        f"Coached: {coached_avg:.0f}  "
        f"({improvement_avg:+.0f})"
    )
    print(f"{'=' * 70}\n")
