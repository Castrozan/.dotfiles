import sys
from pathlib import Path

from benchmark_baseline import (
    validate_tracked_baseline,
    with_freshness_required,
    write_baseline,
)
from benchmark_report import baseline_report_lines
from benchmark_core import (
    DOTFILES_DIRECTORY,
    RESULTS_DIRECTORY,
    TRACKED_BASELINE_DIRECTORY,
    BenchmarkTarget,
    CommandMeasurement,
    aggregate_values_by_key,
    append_result_row,
    ensure_results_file_exists,
    get_current_git_short_commit,
    measure_shell_command,
    recent_result_table_lines,
    required_benchmark_target,
    utc_baseline_timestamp,
)

BASELINE_PATH = TRACKED_BASELINE_DIRECTORY / "baseline.json"
RESULTS_FILE_NAME = "rebuild-times.csv"
CSV_HEADER = "timestamp,type,config,duration_seconds,commit"
SAVE_BASELINE_COMMAND = "benchmark-rebuild --save-baseline"

REGRESSION_THRESHOLD_PERCENT = 150
RECENT_RESULT_ROW_LIMIT = 20


def get_results_file_path() -> Path:
    return RESULTS_DIRECTORY / RESULTS_FILE_NAME


def configuration_label(target: BenchmarkTarget) -> str:
    return f"{target.host}/{target.configuration}"


def get_benchmark_commands(target: BenchmarkTarget) -> dict[str, str]:
    dotfiles = str(DOTFILES_DIRECTORY)
    return {
        "eval": f"nix flake check {dotfiles} --no-build",
        "dry-run": (f"nix build {dotfiles}#{target.flake_output} --dry-run"),
        "build": f"nix build {dotfiles}#{target.flake_output}",
        "rebuild": "rebuild",
    }


def record_benchmark_result(
    results_file: Path,
    benchmark_type: str,
    configuration: str,
    duration_seconds: float,
    commit_hash: str,
) -> None:
    append_result_row(
        results_file,
        [
            benchmark_type,
            configuration,
            f"{duration_seconds:.3f}",
            commit_hash,
        ],
    )


def run_and_record_benchmark(
    benchmark_type: str,
    command: str,
    configuration: str,
    results_file: Path,
) -> CommandMeasurement:
    print(f"Benchmarking: {benchmark_type} ({configuration})")
    measurement = measure_shell_command(command)

    if not measurement.succeeded:
        print(
            f"  Command failed after {measurement.elapsed_seconds:.2f}s; "
            "no result recorded"
        )
        return measurement

    record_benchmark_result(
        results_file,
        benchmark_type,
        configuration,
        measurement.elapsed_seconds,
        get_current_git_short_commit(),
    )
    print(f"  Duration: {measurement.elapsed_seconds:.2f}s")
    return measurement


def build_baseline_from_measurements(
    measurements: dict[str, float],
    target: BenchmarkTarget,
) -> dict:
    return {
        "generated_at": utc_baseline_timestamp(),
        "git_commit": get_current_git_short_commit(),
        "host": target.host,
        "config": target.configuration,
        "threshold_percent": REGRESSION_THRESHOLD_PERCENT,
        "measurements": {
            benchmark_type: {
                "duration_seconds": round(duration, 3),
                "max_allowed_seconds": round(
                    duration * REGRESSION_THRESHOLD_PERCENT / 100,
                    3,
                ),
            }
            for benchmark_type, duration in measurements.items()
        },
    }


def save_baseline(
    benchmark_commands: dict[str, str],
    target: BenchmarkTarget,
    results_file: Path,
) -> bool:
    measurements: dict[str, float] = {}
    for benchmark_type in ("eval", "rebuild"):
        measurement = run_and_record_benchmark(
            benchmark_type,
            benchmark_commands[benchmark_type],
            configuration_label(target),
            results_file,
        )
        if not measurement.succeeded:
            print(f"\nBaseline not saved: the {benchmark_type} command failed.")
            return False
        measurements[benchmark_type] = measurement.elapsed_seconds

    baseline = build_baseline_from_measurements(measurements, target)
    write_baseline(BASELINE_PATH, baseline)

    print(f"\nBaseline saved to {BASELINE_PATH}")
    print(f"  Host: {baseline['host']}/{baseline['config']}")
    print(f"  Commit: {baseline['git_commit']}")
    print(f"  Threshold: {REGRESSION_THRESHOLD_PERCENT}% of measured values")
    for name, data in baseline["measurements"].items():
        print(
            f"  {name}: {data['duration_seconds']:.1f}s "
            f"(max {data['max_allowed_seconds']:.1f}s)"
        )
    return True


def check_baseline(require_fresh: bool) -> bool:
    validation = validate_tracked_baseline(
        BASELINE_PATH,
        "duration_seconds",
        "max_allowed_seconds",
        SAVE_BASELINE_COMMAND,
    )
    if require_fresh:
        validation = with_freshness_required(validation, SAVE_BASELINE_COMMAND)
    for line in baseline_report_lines("REBUILD PERFORMANCE BASELINE CHECK", validation):
        print(line)

    if validation.failures:
        return False

    for name, data in validation.document["measurements"].items():
        print(
            f"  {name}: {data['duration_seconds']:.1f}s "
            f"(max {data['max_allowed_seconds']:.1f}s)"
        )

    print("\nPASSED: Baseline is valid.")
    return True


def print_recent_results(results_file: Path) -> None:
    lines = results_file.read_text().splitlines() if results_file.exists() else []
    if len(lines) <= 1:
        print("No benchmark results found.")
        return

    print("=== Recent Benchmark Results ===")
    for row in recent_result_table_lines(lines, RECENT_RESULT_ROW_LIMIT):
        print(row)

    print()
    print_averages_by_type(lines[1:])


def print_averages_by_type(data_lines: list[str]) -> None:
    print("=== Averages by Type ===")
    averages = aggregate_values_by_key(data_lines, (1, 2), 3)
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
        passed = check_baseline("--require-fresh" in sys.argv)
        raise SystemExit(0 if passed else 1)

    results_file = get_results_file_path()
    ensure_results_file_exists(results_file, CSV_HEADER)

    if sys.argv[1:2] == ["report"]:
        print_recent_results(results_file)
        return

    target = required_benchmark_target()
    benchmark_commands = get_benchmark_commands(target)

    if "--save-baseline" in sys.argv:
        if not save_baseline(benchmark_commands, target, results_file):
            raise SystemExit(1)
        return

    command = sys.argv[1] if len(sys.argv) > 1 else "all"

    if command == "all":
        for benchmark_type in ("eval", "dry-run"):
            run_and_record_benchmark(
                benchmark_type,
                benchmark_commands[benchmark_type],
                configuration_label(target),
                results_file,
            )
    elif command in benchmark_commands:
        run_and_record_benchmark(
            command,
            benchmark_commands[command],
            configuration_label(target),
            results_file,
        )
    else:
        print_usage()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
