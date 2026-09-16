import pathlib

import benchmark_baseline
import benchmark_core
import benchmark_report
import desktop_benchmarks.results

BASELINE_PATH = benchmark_core.TRACKED_BASELINE_DIRECTORY / "baseline-desktop.json"


SAVE_BASELINE_COMMAND = "benchmark-desktop --save-baseline"


REGRESSION_THRESHOLD_PERCENT = 200


def save_baseline(results: list[dict]) -> bool:
    measurements = {}
    for r in results:
        if r["error"]:
            continue
        measurements[r["name"]] = {
            "avg_ms": round(r["avg"], 1),
            "max_allowed_ms": round(r["avg"] * REGRESSION_THRESHOLD_PERCENT / 100, 1),
        }

    if not measurements:
        print("\nBaseline not saved: every measured component failed.")
        return False

    target = benchmark_core.required_benchmark_target()
    baseline = {
        "generated_at": benchmark_core.utc_baseline_timestamp(),
        "git_commit": benchmark_core.get_current_git_short_commit(),
        "host": target.host,
        "config": target.configuration,
        "threshold_percent": REGRESSION_THRESHOLD_PERCENT,
        "measurements": measurements,
    }
    benchmark_baseline.write_baseline(BASELINE_PATH, baseline)

    print(f"\nBaseline saved to {BASELINE_PATH}")
    print(f"  Host: {baseline['host']}/{baseline['config']}")
    print(f"  Commit: {baseline['git_commit']}")
    print(f"  Threshold: {REGRESSION_THRESHOLD_PERCENT}%")
    for name, data in measurements.items():
        print(
            f"  {name}: {desktop_benchmarks.results.format_ms(data['avg_ms'])} "
            f"(max {desktop_benchmarks.results.format_ms(data['max_allowed_ms'])})"
        )
    return True


def tracked_baseline_validation() -> benchmark_baseline.BaselineValidation:
    return benchmark_baseline.validate_tracked_baseline(
        BASELINE_PATH,
        "avg_ms",
        "max_allowed_ms",
        SAVE_BASELINE_COMMAND,
    )


def check_baseline(require_fresh: bool) -> bool:
    validation = tracked_baseline_validation()
    if require_fresh:
        validation = benchmark_baseline.with_freshness_required(
            validation, SAVE_BASELINE_COMMAND
        )
    for line in benchmark_report.baseline_report_lines(
        "DESKTOP PERFORMANCE BASELINE CHECK", validation
    ):
        print(line)
    if validation.failures:
        return False

    print()
    print(f"  {'Component':<22} {'Baseline':>10} {'Max':>10}")
    print(f"  {'-' * 44}")
    for name, data in validation.document["measurements"].items():
        print(
            f"  {name:<22} "
            f"{desktop_benchmarks.results.format_ms(data['avg_ms']):>10} "
            f"{desktop_benchmarks.results.format_ms(data['max_allowed_ms']):>10}"
        )

    print("\nPASSED: Baseline is valid.")
    return True


def compare_latest_to_baseline(results_file: pathlib.Path) -> bool:
    gated = benchmark_baseline.with_freshness_required(
        tracked_baseline_validation(),
        SAVE_BASELINE_COMMAND,
    )
    for line in benchmark_report.baseline_report_lines(
        "DESKTOP PERFORMANCE REGRESSION CHECK", gated
    ):
        print(line)
    if gated.failures:
        return False

    print()
    if not results_file.exists():
        print(
            f"FAILED: no measured results at {results_file}. "
            "Run 'benchmark-desktop' on this machine before comparing."
        )
        return False

    measured_values = benchmark_core.latest_value_by_key(
        results_file.read_text().splitlines()[1:], (1,), 2
    )
    comparison = benchmark_baseline.compare_measured_values(
        gated.document, measured_values, "max_allowed_ms"
    )

    for name in comparison.missing_names:
        print(f"  MISSING  {name}: the latest run measured nothing")
    for name in comparison.exceeded_names:
        ceiling_ms = gated.document["measurements"][name]["max_allowed_ms"]
        print(
            f"  SLOWER   {name}: {desktop_benchmarks.results.format_ms(measured_values[name])} exceeds "
            f"max {desktop_benchmarks.results.format_ms(ceiling_ms)}"
        )

    if comparison.exceeded_names or comparison.missing_names:
        print(
            f"\nFAILED: {len(comparison.exceeded_names)} regressions, "
            f"{len(comparison.missing_names)} unmeasured components."
        )
        return False

    print("PASSED: every tracked component is within its ceiling.")
    return True
