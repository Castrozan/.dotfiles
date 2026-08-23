import sys
from pathlib import Path

from benchmark_baseline import validate_tracked_baseline, write_baseline
from benchmark_core import (
    DOTFILES_DIRECTORY,
    RESULTS_DIRECTORY,
    TRACKED_BASELINE_DIRECTORY,
    BenchmarkTarget,
    CommandMeasurement,
    append_result_row,
    ensure_results_file_exists,
    get_current_git_short_commit,
    measure_shell_command,
    required_benchmark_target,
    utc_baseline_timestamp,
)

BASELINE_PATH = TRACKED_BASELINE_DIRECTORY / "baseline.json"
RESULTS_FILE_NAME = "rebuild-times.csv"
CSV_HEADER = "timestamp,type,config,duration_seconds,commit"
SAVE_BASELINE_COMMAND = "benchmark-rebuild --save-baseline"

REGRESSION_THRESHOLD_PERCENT = 150


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


def check_baseline() -> bool:
    validation = validate_tracked_baseline(
        BASELINE_PATH,
        "duration_seconds",
        "max_allowed_seconds",
        SAVE_BASELINE_COMMAND,
    )
    baseline = validation.document

    print("=" * 60)
    print("REBUILD PERFORMANCE BASELINE CHECK")
    print("=" * 60)
    print(f"  Generated: {baseline.get('generated_at', 'unknown')}")
    print(f"  Age: {_describe_age(validation.age_days)}")
    print(f"  Commit: {baseline.get('git_commit', 'unknown')}")
    print(
        f"  Host: {baseline.get('host', 'unknown')}/{baseline.get('config', 'unknown')}"
    )
    print(f"  Threshold: {baseline.get('threshold_percent', '?')}%")

    if validation.failures:
        print(f"\nFAILED ({len(validation.failures)} issues):")
        for failure in validation.failures:
            print(f"  - {failure}")
        return False

    for name, data in baseline["measurements"].items():
        print(
            f"  {name}: {data['duration_seconds']:.1f}s "
            f"(max {data['max_allowed_seconds']:.1f}s)"
        )

    print("\nPASSED: Baseline is valid.")
    return True


def _describe_age(age_days: int | None) -> str:
    if age_days is None:
        return "unknown"
    return f"{age_days} days"


def print_recent_results(results_file: Path) -> None:
    if not results_file.exists():
        print("No benchmark results found.")
        return

    lines = results_file.read_text().splitlines()
    if len(lines) <= 1:
        print("No benchmark results found.")
        return

    print("=== Recent Benchmark Results ===")
    header = lines[0].split(",")
    recent_lines = lines[-20:] if len(lines) > 21 else lines[1:]

    column_widths = [len(column) for column in header]
    parsed_rows = []
    for line in recent_lines:
        fields = line.split(",")
        parsed_rows.append(fields)
        for i, field in enumerate(fields):
            if i < len(column_widths):
                column_widths[i] = max(column_widths[i], len(field))

    format_string = "  ".join(f"{{:<{width}}}" for width in column_widths)
    print(format_string.format(*header))
    for row in parsed_rows:
        print(format_string.format(*row))

    print()
    print_averages_by_type(lines[1:])


def print_averages_by_type(
    data_lines: list[str],
) -> None:
    print("=== Averages by Type ===")
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}

    for line in data_lines:
        fields = line.split(",")
        if len(fields) < 4:
            continue
        key = f"{fields[1]},{fields[2]}"
        try:
            duration = float(fields[3])
        except ValueError:
            continue
        totals[key] = totals.get(key, 0.0) + duration
        counts[key] = counts.get(key, 0) + 1

    for key in sorted(totals):
        average = totals[key] / counts[key]
        print(f"  {key}: {average:.2f}s avg ({counts[key]} runs)")


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
        passed = check_baseline()
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
