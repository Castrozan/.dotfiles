import pathlib

import benchmark_baseline
import benchmark_core
import benchmark_report
import rebuild_benchmarks.execution

BASELINE_PATH = benchmark_core.TRACKED_BASELINE_DIRECTORY / "baseline.json"


SAVE_BASELINE_COMMAND = "benchmark-rebuild --save-baseline"


REGRESSION_THRESHOLD_PERCENT = 150


def build_baseline_from_measurements(
    measurements: dict[str, float],
    target: benchmark_core.BenchmarkTarget,
) -> dict:
    return {
        "generated_at": benchmark_core.utc_baseline_timestamp(),
        "git_commit": benchmark_core.get_current_git_short_commit(),
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
    target: benchmark_core.BenchmarkTarget,
    results_file: pathlib.Path,
) -> bool:
    measurements: dict[str, float] = {}
    for benchmark_type in ("eval", "rebuild"):
        measurement = rebuild_benchmarks.execution.run_and_record_benchmark(
            benchmark_type,
            benchmark_commands[benchmark_type],
            rebuild_benchmarks.execution.configuration_label(target),
            results_file,
        )
        if not measurement.succeeded:
            print(f"\nBaseline not saved: the {benchmark_type} command failed.")
            return False
        measurements[benchmark_type] = measurement.elapsed_seconds

    baseline = build_baseline_from_measurements(measurements, target)
    benchmark_baseline.write_baseline(BASELINE_PATH, baseline)

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
    validation = benchmark_baseline.validate_tracked_baseline(
        BASELINE_PATH,
        "duration_seconds",
        "max_allowed_seconds",
        SAVE_BASELINE_COMMAND,
    )
    if require_fresh:
        validation = benchmark_baseline.with_freshness_required(
            validation, SAVE_BASELINE_COMMAND
        )
    for line in benchmark_report.baseline_report_lines(
        "REBUILD PERFORMANCE BASELINE CHECK", validation
    ):
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
