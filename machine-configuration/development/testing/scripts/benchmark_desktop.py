import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from benchmark_baseline import validate_tracked_baseline, write_baseline
from benchmark_core import (
    DOTFILES_DIRECTORY,
    RESULTS_DIRECTORY,
    TRACKED_BASELINE_DIRECTORY,
    CommandMeasurement,
    append_result_row,
    ensure_results_file_exists,
    get_current_git_short_commit,
    measure_command,
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

DEFAULT_COMMAND_TIMEOUT_SECONDS = 10.0
QUICKSHELL_TIMEOUT_SECONDS = 5.0
QUICKSHELL_SETTLE_SECONDS = 0.15
WINDOW_SWITCHER_SETTLE_SECONDS = 0.1

QS_BAR_PATH = str(DOTFILES_DIRECTORY / ".config" / "quickshell" / "bar")


@dataclass(frozen=True)
class BaselineComparison:
    regression_messages: list[str]
    missing_component_names: list[str]


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


def get_latest_results_by_component(results_file: Path) -> dict[str, float]:
    if not results_file.exists():
        return {}

    lines = results_file.read_text().splitlines()
    latest: dict[str, float] = {}
    for line in lines[1:]:
        fields = line.split(",")
        if len(fields) < 3:
            continue
        try:
            latest[fields[1]] = float(fields[2])
        except ValueError:
            continue
    return latest


def compare_latest_results_to_baseline(
    baseline: dict,
    latest_results: dict[str, float],
) -> BaselineComparison:
    regression_messages: list[str] = []
    missing_component_names: list[str] = []

    for name, data in baseline.get("measurements", {}).items():
        actual_ms = latest_results.get(name)
        if actual_ms is None:
            missing_component_names.append(name)
            continue
        max_allowed_ms = data["max_allowed_ms"]
        if actual_ms > max_allowed_ms:
            regression_messages.append(
                f"{name}: {format_ms(actual_ms)} exceeds "
                f"max {format_ms(max_allowed_ms)}"
            )

    return BaselineComparison(regression_messages, missing_component_names)


def validated_tracked_baseline(title: str) -> dict | None:
    validation = validate_tracked_baseline(
        BASELINE_PATH,
        "avg_ms",
        "max_allowed_ms",
        SAVE_BASELINE_COMMAND,
    )
    baseline = validation.document
    generated_at = baseline.get("generated_at", "unknown")
    age_text = "unknown" if validation.age_days is None else f"{validation.age_days}"

    print("=" * 60)
    print(title)
    print("=" * 60)
    print(f"  Baseline: {generated_at} (age: {age_text} days)")
    print(f"  Commit: {baseline.get('git_commit', 'unknown')}")
    print(
        f"  Host: {baseline.get('host', 'unknown')}/{baseline.get('config', 'unknown')}"
    )
    print(f"  Threshold: {baseline.get('threshold_percent', '?')}%")
    print()

    if validation.failures:
        print(f"FAILED ({len(validation.failures)} issues):")
        for failure in validation.failures:
            print(f"  - {failure}")
        return None
    return baseline


def check_baseline() -> bool:
    baseline = validated_tracked_baseline("DESKTOP PERFORMANCE BASELINE CHECK")
    if baseline is None:
        return False

    print(f"  {'Component':<22} {'Baseline':>10} {'Max':>10}")
    print(f"  {'-' * 44}")
    for name, data in baseline["measurements"].items():
        print(
            f"  {name:<22} "
            f"{format_ms(data['avg_ms']):>10} "
            f"{format_ms(data['max_allowed_ms']):>10}"
        )

    print("\nPASSED: Baseline is valid.")
    return True


def compare_latest_to_baseline(results_file: Path) -> bool:
    baseline = validated_tracked_baseline("DESKTOP PERFORMANCE REGRESSION CHECK")
    if baseline is None:
        return False

    if not results_file.exists():
        print(
            f"FAILED: no measured results at {results_file}. "
            "Run 'benchmark-desktop' on this machine before comparing."
        )
        return False

    comparison = compare_latest_results_to_baseline(
        baseline,
        get_latest_results_by_component(results_file),
    )

    for name in comparison.missing_component_names:
        print(f"  MISSING  {name}: the latest run measured nothing")
    for message in comparison.regression_messages:
        print(f"  SLOWER   {message}")

    if comparison.missing_component_names or comparison.regression_messages:
        print(
            f"\nFAILED: {len(comparison.regression_messages)} regressions, "
            f"{len(comparison.missing_component_names)} unmeasured components."
        )
        return False

    print("PASSED: every tracked component is within its ceiling.")
    return True


def print_report(results_file: Path) -> None:
    if not results_file.exists():
        print("No benchmark results found.")
        return

    lines = results_file.read_text().splitlines()
    if len(lines) <= 1:
        print("No benchmark results found.")
        return

    print("=== Recent Desktop Benchmark Results ===")
    header = lines[0].split(",")
    recent = lines[-30:] if len(lines) > 31 else lines[1:]

    widths = [len(c) for c in header]
    rows = []
    for line in recent:
        fields = line.split(",")
        rows.append(fields)
        for i, field in enumerate(fields):
            if i < len(widths):
                widths[i] = max(widths[i], len(field))

    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*header))
    for row in rows:
        print(fmt.format(*row))

    print()
    _print_averages(lines[1:])


def _print_averages(data_lines: list[str]) -> None:
    print("=== Averages by Component ===")
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}

    for line in data_lines:
        fields = line.split(",")
        if len(fields) < 3:
            continue
        name = fields[1]
        try:
            avg = float(fields[2])
        except ValueError:
            continue
        totals[name] = totals.get(name, 0.0) + avg
        counts[name] = counts.get(name, 0) + 1

    for name in sorted(totals):
        avg = totals[name] / counts[name]
        print(f"  {name}: {format_ms(avg)} avg ({counts[name]} runs)")


def parse_arguments(argv: list[str]) -> tuple[str, int, str | None]:
    if "--save-baseline" in argv:
        return "save-baseline", DEFAULT_ITERATIONS, None
    if "--check-baseline" in argv:
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

    if command == "check-baseline":
        passed = check_baseline()
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
