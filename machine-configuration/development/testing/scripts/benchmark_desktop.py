import sys

import benchmark_core
import desktop_benchmarks.baseline
import desktop_benchmarks.catalog
import desktop_benchmarks.results

DEFAULT_ITERATIONS = 5


def parse_arguments(argv: list[str]) -> tuple[str, int, str | None]:
    if "--save-baseline" in argv:
        return "save-baseline", DEFAULT_ITERATIONS, None
    if "--check-baseline" in argv:
        if "--require-fresh" in argv:
            return "check-baseline-fresh", 0, None
        return "check-baseline", 0, None
    if "--compare-latest" in argv:
        return "compare-latest", 0, None

    command = "run"
    iterations = DEFAULT_ITERATIONS
    component = None

    args = list(argv)
    if args and args[0] == "report":
        return "report", 0, None

    for arg in args:
        try:
            iterations = int(arg)
        except ValueError:
            component = arg

    return command, iterations, component


def filter_benchmarks(
    benchmarks: list[tuple[str, object]], component: str | None
) -> list[tuple[str, object]]:
    if component is None:
        return benchmarks
    return [(n, f) for n, f in benchmarks if component in n]


def print_usage() -> None:
    print("Usage: benchmark-desktop [iterations] [component]")
    print()
    print("Commands:")
    print("  [default]          - Run all available benchmarks")
    print("  report             - Show benchmark history")
    print()
    print("Flags:")
    print("  --save-baseline    - Measure and save baseline")
    print("  --check-baseline   - Validate committed baseline")
    print("  --compare-latest   - Compare the latest measured run to the baseline")
    print()
    print("Components (partial match):")
    print("  hyprctl, workspace, switcher, launcher, dashboard,")
    print("  sidebar, overview, volume, fuzzel, wezterm, tmux")
    print()
    print("Examples:")
    print("  benchmark-desktop              # all, 5 iterations")
    print("  benchmark-desktop 10           # all, 10 iterations")
    print("  benchmark-desktop 10 tmux      # tmux only, 10 iterations")
    print("  benchmark-desktop workspace    # workspace only, 5 iterations")


def main() -> None:
    command, iterations, component = parse_arguments(sys.argv[1:])

    if command in ("check-baseline", "check-baseline-fresh"):
        passed = desktop_benchmarks.baseline.check_baseline(
            command == "check-baseline-fresh"
        )
        raise SystemExit(0 if passed else 1)

    results_file = desktop_benchmarks.results.get_results_file_path()

    if command == "compare-latest":
        passed = desktop_benchmarks.baseline.compare_latest_to_baseline(results_file)
        raise SystemExit(0 if passed else 1)

    benchmark_core.ensure_results_file_exists(
        results_file, desktop_benchmarks.results.CSV_HEADER
    )

    if command == "report":
        desktop_benchmarks.results.print_report(results_file)
        return

    available = desktop_benchmarks.catalog.get_available_benchmarks()
    benchmarks = filter_benchmarks(available, component)

    if not benchmarks:
        if component:
            print(f"No benchmarks matching '{component}'")
        else:
            print("No benchmarks available")
        print_usage()
        raise SystemExit(1)

    hyprland = desktop_benchmarks.catalog.is_hyprland_running()
    print("=== Desktop Performance Benchmark ===")
    print(f"  Hyprland: {'yes' if hyprland else 'no (terminal-only mode)'}")
    print(f"  Iterations: {iterations}")
    print(f"  Components: {len(benchmarks)}")
    print()

    results = desktop_benchmarks.results.run_benchmarks(
        benchmarks, iterations, results_file
    )
    desktop_benchmarks.results.print_summary(results)

    if command == "save-baseline":
        if not desktop_benchmarks.baseline.save_baseline(results):
            raise SystemExit(1)
    else:
        print(f"\nResults saved to {results_file}")


if __name__ == "__main__":
    main()
