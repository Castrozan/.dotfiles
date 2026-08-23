import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from benchmark_baseline import (
    BaselineValidation,
    compare_measured_values,
    validate_tracked_baseline,
    with_freshness_required,
    write_baseline,
)
from benchmark_report import baseline_report_lines
from benchmark_core import (
    DOTFILES_DIRECTORY,
    RESULTS_DIRECTORY,
    TRACKED_BASELINE_DIRECTORY,
    CommandMeasurement,
    aggregate_values_by_key,
    append_result_row,
    ensure_results_file_exists,
    get_current_git_short_commit,
    latest_value_by_key,
    measure_command,
    recent_result_table_lines,
    required_benchmark_target,
    unmeasurable_command,
    utc_baseline_timestamp,
)

RESULTS_FILE_NAME = "desktop-times.csv"
CSV_HEADER = "timestamp,component,avg_ms,min_ms,max_ms,iterations"

BASELINE_PATH = TRACKED_BASELINE_DIRECTORY / "baseline-desktop.json"
SAVE_BASELINE_COMMAND = "benchmark-desktop --save-baseline"

DEFAULT_ITERATIONS = 5
REGRESSION_THRESHOLD_PERCENT = 200
RECENT_RESULT_ROW_LIMIT = 30

DEFAULT_COMMAND_TIMEOUT_SECONDS = 10.0
QUICKSHELL_TIMEOUT_SECONDS = 5.0
QUICKSHELL_SETTLE_SECONDS = 0.15
WINDOW_SWITCHER_SETTLE_SECONDS = 0.1

QS_BAR_PATH = str(DOTFILES_DIRECTORY / ".config" / "quickshell" / "bar")


def is_hyprland_running() -> bool:
    return bool(os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"))


def get_results_file_path() -> Path:
    return RESULTS_DIRECTORY / RESULTS_FILE_NAME


def run_cleanup_command(arguments: list[str], timeout_seconds: float | None) -> None:
    subprocess.run(
        arguments,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=timeout_seconds,
    )


def measure_iterations(
    name: str,
    measure_fn,
    iterations: int,
) -> dict:
    times: list[float] = []
    for _ in range(iterations):
        try:
            measurement = measure_fn()
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError):
            measurement = unmeasurable_command()
        if measurement.succeeded:
            times.append(measurement.elapsed_seconds * 1000)
        print(".", end="", flush=True)
    print()

    if not times:
        return {"name": name, "avg": 0, "min": 0, "max": 0, "times": [], "error": True}

    return {
        "name": name,
        "avg": sum(times) / len(times),
        "min": min(times),
        "max": max(times),
        "times": times,
        "error": False,
    }


def quickshell_bar_call(target: str, action: str) -> list[str]:
    return ["qs", "-p", QS_BAR_PATH, "ipc", "call", target, action]


def quickshell_config_call(
    configuration: str,
    target: str,
    action: str,
) -> list[str]:
    return ["qs", "-c", configuration, "ipc", "call", target, action]


def measure_quickshell_toggle(
    open_arguments: list[str],
    close_arguments: list[str],
    settle_seconds: float,
) -> CommandMeasurement:
    measurement = measure_command(
        open_arguments,
        timeout_seconds=QUICKSHELL_TIMEOUT_SECONDS,
    )
    time.sleep(settle_seconds)
    run_cleanup_command(close_arguments, QUICKSHELL_TIMEOUT_SECONDS)
    return measurement


def measure_process_launch(
    arguments: list[str],
    settle_seconds: float,
    terminate_timeout_seconds: float,
) -> CommandMeasurement:
    start_time = time.perf_counter()
    process = subprocess.Popen(
        arguments,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(settle_seconds)
    elapsed_seconds = time.perf_counter() - start_time
    early_exit_status = process.poll()
    process.terminate()
    process.wait(timeout=terminate_timeout_seconds)
    return CommandMeasurement(
        succeeded=early_exit_status in (None, 0),
        elapsed_seconds=elapsed_seconds,
    )


def bench_hyprctl_ipc() -> CommandMeasurement:
    return measure_command(
        ["hyprctl", "version"],
        timeout_seconds=DEFAULT_COMMAND_TIMEOUT_SECONDS,
    )


def bench_hyprctl_clients() -> CommandMeasurement:
    return measure_command(
        ["hyprctl", "clients", "-j"],
        timeout_seconds=DEFAULT_COMMAND_TIMEOUT_SECONDS,
    )


def bench_workspace_switch() -> CommandMeasurement:
    active_workspace = subprocess.run(
        ["hyprctl", "activeworkspace", "-j"],
        capture_output=True,
        text=True,
    )
    if active_workspace.returncode != 0:
        return unmeasurable_command()

    current = json.loads(active_workspace.stdout)["id"]
    target = current + 1 if current < 10 else current - 1
    measurement = measure_command(
        ["hyprctl", "dispatch", "workspace", str(target)],
        timeout_seconds=DEFAULT_COMMAND_TIMEOUT_SECONDS,
    )
    run_cleanup_command(["hyprctl", "dispatch", "workspace", str(current)], None)
    return measurement


def bench_window_switcher() -> CommandMeasurement:
    return measure_quickshell_toggle(
        quickshell_config_call("switcher", "switcher", "open"),
        quickshell_config_call("switcher", "switcher", "cancel"),
        WINDOW_SWITCHER_SETTLE_SECONDS,
    )


def bench_launcher_qs() -> CommandMeasurement:
    return measure_quickshell_toggle(
        quickshell_bar_call("launcher", "toggle"),
        quickshell_bar_call("launcher", "toggle"),
        QUICKSHELL_SETTLE_SECONDS,
    )


def bench_dashboard() -> CommandMeasurement:
    return measure_quickshell_toggle(
        quickshell_bar_call("dashboard", "toggle"),
        quickshell_bar_call("dashboard", "toggle"),
        QUICKSHELL_SETTLE_SECONDS,
    )


def bench_sidebar() -> CommandMeasurement:
    return measure_quickshell_toggle(
        quickshell_bar_call("sidebar", "toggle"),
        quickshell_bar_call("sidebar", "toggle"),
        QUICKSHELL_SETTLE_SECONDS,
    )


def bench_workspace_overview() -> CommandMeasurement:
    return measure_quickshell_toggle(
        quickshell_config_call("overview", "overview", "toggle"),
        quickshell_config_call("overview", "overview", "toggle"),
        QUICKSHELL_SETTLE_SECONDS,
    )


def bench_volume_control() -> CommandMeasurement:
    measurement = measure_command(
        ["volume", "--inc"],
        timeout_seconds=DEFAULT_COMMAND_TIMEOUT_SECONDS,
    )
    run_cleanup_command(["volume", "--dec"], None)
    return measurement


def bench_fuzzel_launch() -> CommandMeasurement:
    if not shutil.which("fuzzel"):
        return unmeasurable_command()
    return measure_process_launch(["fuzzel"], 0.3, 3)


def bench_wezterm_launch() -> CommandMeasurement:
    measurement = measure_process_launch(
        ["wezterm", "start", "--", "sleep", "0.5"],
        1.5,
        5,
    )
    time.sleep(0.3)
    return measurement


def bench_tmux_new_session() -> CommandMeasurement:
    session_name = "_bench_perf_test"
    measurement = measure_command(
        ["tmux", "new-session", "-d", "-s", session_name],
        timeout_seconds=QUICKSHELL_TIMEOUT_SECONDS,
    )
    run_cleanup_command(["tmux", "kill-session", "-t", session_name], None)
    return measurement


def bench_tmux_split() -> CommandMeasurement:
    session_name = "_bench_perf_split"
    started = measure_command(
        ["tmux", "new-session", "-d", "-s", session_name],
        timeout_seconds=QUICKSHELL_TIMEOUT_SECONDS,
    )
    if not started.succeeded:
        return unmeasurable_command()

    measurement = measure_command(
        ["tmux", "split-window", "-t", session_name],
        timeout_seconds=QUICKSHELL_TIMEOUT_SECONDS,
    )
    run_cleanup_command(["tmux", "kill-session", "-t", session_name], None)
    return measurement


BENCHMARKS_HYPRLAND = [
    ("hyprctl-ipc", bench_hyprctl_ipc),
    ("hyprctl-clients", bench_hyprctl_clients),
    ("workspace-switch", bench_workspace_switch),
    ("window-switcher", bench_window_switcher),
    ("launcher-qs", bench_launcher_qs),
    ("dashboard", bench_dashboard),
    ("sidebar", bench_sidebar),
    ("workspace-overview", bench_workspace_overview),
    ("volume-control", bench_volume_control),
    ("fuzzel", bench_fuzzel_launch),
]

BENCHMARKS_TERMINAL = [
    ("wezterm-launch", bench_wezterm_launch),
    ("tmux-new-session", bench_tmux_new_session),
    ("tmux-split-window", bench_tmux_split),
]

ALL_BENCHMARKS = BENCHMARKS_HYPRLAND + BENCHMARKS_TERMINAL


def get_available_benchmarks() -> list[tuple[str, object]]:
    if is_hyprland_running():
        return ALL_BENCHMARKS
    return BENCHMARKS_TERMINAL


def record_result(
    results_file: Path,
    name: str,
    avg_ms: float,
    min_ms: float,
    max_ms: float,
    iterations: int,
) -> None:
    append_result_row(
        results_file,
        [
            name,
            f"{avg_ms:.1f}",
            f"{min_ms:.1f}",
            f"{max_ms:.1f}",
            str(iterations),
        ],
    )


def format_ms(ms: float) -> str:
    if ms < 1000:
        return f"{ms:.0f}ms"
    return f"{ms / 1000:.2f}s"


def run_benchmarks(
    benchmarks: list[tuple[str, object]],
    iterations: int,
    results_file: Path,
) -> list[dict]:
    results = []
    for name, fn in benchmarks:
        print(f"  {name} ({iterations}x) ", end="", flush=True)
        result = measure_iterations(name, fn, iterations)
        results.append(result)

        if result["error"]:
            print("    FAILED (all iterations errored)")
        else:
            print(
                f"    avg={format_ms(result['avg'])}  "
                f"min={format_ms(result['min'])}  "
                f"max={format_ms(result['max'])}"
            )
            record_result(
                results_file,
                name,
                result["avg"],
                result["min"],
                result["max"],
                len(result["times"]),
            )

    return results


def print_summary(results: list[dict]) -> None:
    print()
    print("=" * 62)
    print(f"{'Component':<22} {'Avg':>8} {'Min':>8} {'Max':>8}")
    print("-" * 62)
    for r in results:
        if r["error"]:
            print(f"{r['name']:<22} {'FAILED':>8}")
        else:
            print(
                f"{r['name']:<22} "
                f"{format_ms(r['avg']):>8} "
                f"{format_ms(r['min']):>8} "
                f"{format_ms(r['max']):>8}"
            )
    print("=" * 62)


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

    target = required_benchmark_target()
    baseline = {
        "generated_at": utc_baseline_timestamp(),
        "git_commit": get_current_git_short_commit(),
        "host": target.host,
        "config": target.configuration,
        "threshold_percent": REGRESSION_THRESHOLD_PERCENT,
        "measurements": measurements,
    }
    write_baseline(BASELINE_PATH, baseline)

    print(f"\nBaseline saved to {BASELINE_PATH}")
    print(f"  Host: {baseline['host']}/{baseline['config']}")
    print(f"  Commit: {baseline['git_commit']}")
    print(f"  Threshold: {REGRESSION_THRESHOLD_PERCENT}%")
    for name, data in measurements.items():
        print(
            f"  {name}: {format_ms(data['avg_ms'])} "
            f"(max {format_ms(data['max_allowed_ms'])})"
        )
    return True


def tracked_baseline_validation() -> BaselineValidation:
    return validate_tracked_baseline(
        BASELINE_PATH,
        "avg_ms",
        "max_allowed_ms",
        SAVE_BASELINE_COMMAND,
    )


def check_baseline(require_fresh: bool) -> bool:
    validation = tracked_baseline_validation()
    if require_fresh:
        validation = with_freshness_required(validation, SAVE_BASELINE_COMMAND)
    for line in baseline_report_lines("DESKTOP PERFORMANCE BASELINE CHECK", validation):
        print(line)
    if validation.failures:
        return False

    print()
    print(f"  {'Component':<22} {'Baseline':>10} {'Max':>10}")
    print(f"  {'-' * 44}")
    for name, data in validation.document["measurements"].items():
        print(
            f"  {name:<22} "
            f"{format_ms(data['avg_ms']):>10} "
            f"{format_ms(data['max_allowed_ms']):>10}"
        )

    print("\nPASSED: Baseline is valid.")
    return True


def compare_latest_to_baseline(results_file: Path) -> bool:
    gated = with_freshness_required(
        tracked_baseline_validation(),
        SAVE_BASELINE_COMMAND,
    )
    for line in baseline_report_lines("DESKTOP PERFORMANCE REGRESSION CHECK", gated):
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

    measured_values = latest_value_by_key(
        results_file.read_text().splitlines()[1:], (1,), 2
    )
    comparison = compare_measured_values(
        gated.document, measured_values, "max_allowed_ms"
    )

    for name in comparison.missing_names:
        print(f"  MISSING  {name}: the latest run measured nothing")
    for name in comparison.exceeded_names:
        ceiling_ms = gated.document["measurements"][name]["max_allowed_ms"]
        print(
            f"  SLOWER   {name}: {format_ms(measured_values[name])} exceeds "
            f"max {format_ms(ceiling_ms)}"
        )

    if comparison.exceeded_names or comparison.missing_names:
        print(
            f"\nFAILED: {len(comparison.exceeded_names)} regressions, "
            f"{len(comparison.missing_names)} unmeasured components."
        )
        return False

    print("PASSED: every tracked component is within its ceiling.")
    return True


def print_report(results_file: Path) -> None:
    lines = results_file.read_text().splitlines() if results_file.exists() else []
    if len(lines) <= 1:
        print("No benchmark results found.")
        return

    print("=== Recent Desktop Benchmark Results ===")
    for row in recent_result_table_lines(lines, RECENT_RESULT_ROW_LIMIT):
        print(row)

    print()
    _print_averages(lines[1:])


def _print_averages(data_lines: list[str]) -> None:
    print("=== Averages by Component ===")
    averages = aggregate_values_by_key(data_lines, (1,), 2)
    for name, aggregate in sorted(averages.items()):
        print(
            f"  {name}: {format_ms(aggregate.total / aggregate.count)} avg "
            f"({aggregate.count} runs)"
        )


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
        passed = check_baseline(command == "check-baseline-fresh")
        raise SystemExit(0 if passed else 1)

    results_file = get_results_file_path()

    if command == "compare-latest":
        passed = compare_latest_to_baseline(results_file)
        raise SystemExit(0 if passed else 1)

    ensure_results_file_exists(results_file, CSV_HEADER)

    if command == "report":
        print_report(results_file)
        return

    available = get_available_benchmarks()
    benchmarks = filter_benchmarks(available, component)

    if not benchmarks:
        if component:
            print(f"No benchmarks matching '{component}'")
        else:
            print("No benchmarks available")
        print_usage()
        raise SystemExit(1)

    hyprland = is_hyprland_running()
    print("=== Desktop Performance Benchmark ===")
    print(f"  Hyprland: {'yes' if hyprland else 'no (terminal-only mode)'}")
    print(f"  Iterations: {iterations}")
    print(f"  Components: {len(benchmarks)}")
    print()

    results = run_benchmarks(benchmarks, iterations, results_file)
    print_summary(results)

    if command == "save-baseline":
        if not save_baseline(results):
            raise SystemExit(1)
    else:
        print(f"\nResults saved to {results_file}")


if __name__ == "__main__":
    main()
