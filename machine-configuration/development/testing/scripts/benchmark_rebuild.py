import pathlib
import sys

import benchmark_core
import rebuild_benchmarks.baseline
import rebuild_benchmarks.execution

RESULTS_FILE_NAME = "rebuild-times.csv"


CSV_HEADER = "timestamp,type,config,duration_seconds,commit"


RECENT_RESULT_ROW_LIMIT = 20


def get_results_file_path() -> pathlib.Path:
    return benchmark_core.RESULTS_DIRECTORY / RESULTS_FILE_NAME


def print_recent_results(results_file: pathlib.Path) -> None:
    lines = results_file.read_text().splitlines() if results_file.exists() else []
    if len(lines) <= 1:
        print("No benchmark results found.")
        return

    print("=== Recent Benchmark Results ===")
    for row in benchmark_core.recent_result_table_lines(lines, RECENT_RESULT_ROW_LIMIT):
        print(row)

    print()
    print_averages_by_type(lines[1:])


def print_averages_by_type(data_lines: list[str]) -> None:
    print("=== Averages by Type ===")
    averages = benchmark_core.aggregate_values_by_key(data_lines, (1, 2), 3)
    for key, aggregate in sorted(averages.items()):
        average = aggregate.total / aggregate.count
        print(f"  {key}: {average:.2f}s avg ({aggregate.count} runs)")


def print_usage() -> None:
    print("Usage: benchmark-rebuild <command>")
    print()
    print("Commands:")
    print("  eval           - Benchmark flake evaluation")
    print("  dry-run        - Benchmark dry-run build")
    print("  build          - Benchmark full build")
    print("  rebuild        - Benchmark full rebuild")
    print("  all            - Run eval and dry-run")
    print("  report         - Show benchmark history")
    print()
    print("Flags:")
    print("  --save-baseline  - Measure and save baseline")
    print("  --check-baseline - Validate committed baseline")
    print()
    print("The configuration host comes from the nix packaging of this command.")


def main() -> None:
    if "--check-baseline" in sys.argv:
        passed = rebuild_benchmarks.baseline.check_baseline(
            "--require-fresh" in sys.argv
        )
        raise SystemExit(0 if passed else 1)

    results_file = get_results_file_path()
    benchmark_core.ensure_results_file_exists(results_file, CSV_HEADER)

    if sys.argv[1:2] == ["report"]:
        print_recent_results(results_file)
        return

    target = benchmark_core.required_benchmark_target()
    benchmark_commands = rebuild_benchmarks.execution.get_benchmark_commands(target)

    if "--save-baseline" in sys.argv:
        if not rebuild_benchmarks.baseline.save_baseline(
            benchmark_commands, target, results_file
        ):
            raise SystemExit(1)
        return

    command = sys.argv[1] if len(sys.argv) > 1 else "all"

    if command == "all":
        measured_types = ("eval", "dry-run")
    elif command in benchmark_commands:
        measured_types = (command,)
    else:
        print_usage()
        raise SystemExit(1)

    failed_types = [
        benchmark_type
        for benchmark_type in measured_types
        if not rebuild_benchmarks.execution.run_and_record_benchmark(
            benchmark_type,
            benchmark_commands[benchmark_type],
            rebuild_benchmarks.execution.configuration_label(target),
            results_file,
        ).succeeded
    ]
    if failed_types:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
