import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

DOTFILES_DIRECTORY = Path.home() / ".dotfiles"
RESULTS_DIRECTORY = Path.home() / ".local" / "share" / "dotfiles-benchmarks"
RESULTS_FILE_NAME = "desktop-times.csv"
CSV_HEADER = "timestamp,component,avg_ms,min_ms,max_ms,iterations"

BASELINE_PATH = DOTFILES_DIRECTORY / "home" / "modules" / "testing" / "baseline-desktop.json"

DEFAULT_ITERATIONS = 5
REGRESSION_THRESHOLD_PERCENT = 200
MAXIMUM_BASELINE_AGE_DAYS = 30

QS_BAR_PATH = str(DOTFILES_DIRECTORY / ".config" / "quickshell" / "bar")


def is_hyprland_running() -> bool:
    return bool(os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"))


def ensure_results_directory_exists() -> None:
    RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)


def get_results_file_path() -> Path:
    return RESULTS_DIRECTORY / RESULTS_FILE_NAME


def initialize_csv_if_needed(results_file: Path) -> None:
    if not results_file.exists():
        results_file.write_text(CSV_HEADER + "\n")


def run_timed(args: list[str], timeout: float = 10.0) -> float:
    start = time.perf_counter()
    subprocess.run(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=timeout,
    )
    return (time.perf_counter() - start) * 1000


def run_timed_shell(command: str, timeout: float = 10.0) -> float:
    start = time.perf_counter()
    subprocess.run(
        command,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=timeout,
    )
    return (time.perf_counter() - start) * 1000


def measure_iterations(
    name: str,
    measure_fn,
    iterations: int,
) -> dict:
    times: list[float] = []
    for _ in range(iterations):
        try:
            elapsed = measure_fn()
            times.append(elapsed)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError):
            pass
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


def bench_hyprctl_ipc() -> float:
    return run_timed(["hyprctl", "version"])


def bench_hyprctl_clients() -> float:
    return run_timed(["hyprctl", "clients", "-j"])


def bench_workspace_switch() -> float:
    current = json.loads(
        subprocess.run(
            ["hyprctl", "activeworkspace", "-j"],
            capture_output=True,
            text=True,
        ).stdout
    )["id"]
    target = current + 1 if current < 10 else current - 1
    elapsed = run_timed(["hyprctl", "dispatch", "workspace", str(target)])
    subprocess.run(
        ["hyprctl", "dispatch", "workspace", str(current)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return elapsed


def bench_window_switcher() -> float:
    start = time.perf_counter()
    subprocess.run(
        ["qs", "-c", "switcher", "ipc", "call", "switcher", "open"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=5,
    )
    elapsed = (time.perf_counter() - start) * 1000
    time.sleep(0.1)
    subprocess.run(
        ["qs", "-c", "switcher", "ipc", "call", "switcher", "cancel"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=5,
    )
    return elapsed


def bench_launcher_qs() -> float:
    start = time.perf_counter()
    subprocess.run(
        ["qs", "-p", QS_BAR_PATH, "ipc", "call", "launcher", "toggle"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=5,
    )
    elapsed = (time.perf_counter() - start) * 1000
    time.sleep(0.15)
    subprocess.run(
        ["qs", "-p", QS_BAR_PATH, "ipc", "call", "launcher", "toggle"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=5,
    )
    return elapsed


def bench_dashboard() -> float:
    start = time.perf_counter()
    subprocess.run(
        ["qs", "-p", QS_BAR_PATH, "ipc", "call", "dashboard", "toggle"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=5,
    )
    elapsed = (time.perf_counter() - start) * 1000
    time.sleep(0.15)
    subprocess.run(
        ["qs", "-p", QS_BAR_PATH, "ipc", "call", "dashboard", "toggle"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=5,
    )
    return elapsed


def bench_sidebar() -> float:
    start = time.perf_counter()
    subprocess.run(
        ["qs", "-p", QS_BAR_PATH, "ipc", "call", "sidebar", "toggle"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=5,
    )
    elapsed = (time.perf_counter() - start) * 1000
    time.sleep(0.15)
    subprocess.run(
        ["qs", "-p", QS_BAR_PATH, "ipc", "call", "sidebar", "toggle"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=5,
    )
    return elapsed


def bench_workspace_overview() -> float:
    start = time.perf_counter()
    subprocess.run(
        ["qs", "-c", "overview", "ipc", "call", "overview", "toggle"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=5,
    )
    elapsed = (time.perf_counter() - start) * 1000
    time.sleep(0.15)
    subprocess.run(
        ["qs", "-c", "overview", "ipc", "call", "overview", "toggle"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=5,
    )
    return elapsed


def bench_volume_control() -> float:
    elapsed = run_timed(["volume", "--inc"])
    subprocess.run(
        ["volume", "--dec"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return elapsed


def bench_fuzzel_launch() -> float:
    if not shutil.which("fuzzel"):
        return -1
    start = time.perf_counter()
    proc = subprocess.Popen(
        ["fuzzel"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.3)
    elapsed = (time.perf_counter() - start) * 1000
    proc.terminate()
    proc.wait(timeout=3)
    return elapsed


def bench_fish_startup() -> float:
    return run_timed(["fish", "-i", "-c", "exit"])


def bench_wezterm_launch() -> float:
    start = time.perf_counter()
    proc = subprocess.Popen(
        ["wezterm", "start", "--", "sleep", "0.5"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1.5)
    elapsed = (time.perf_counter() - start) * 1000
    proc.terminate()
    proc.wait(timeout=5)
    time.sleep(0.3)
    return elapsed


def bench_tmux_new_session() -> float:
    session_name = "_bench_perf_test"
    start = time.perf_counter()
    subprocess.run(
        ["tmux", "new-session", "-d", "-s", session_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=5,
    )
    elapsed = (time.perf_counter() - start) * 1000
    subprocess.run(
        ["tmux", "kill-session", "-t", session_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return elapsed


def bench_tmux_split() -> float:
    session_name = "_bench_perf_split"
    subprocess.run(
        ["tmux", "new-session", "-d", "-s", session_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=5,
    )
    start = time.perf_counter()
    subprocess.run(
        ["tmux", "split-window", "-t", session_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=5,
    )
    elapsed = (time.perf_counter() - start) * 1000
    subprocess.run(
        ["tmux", "kill-session", "-t", session_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return elapsed


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
    ("fish-startup", bench_fish_startup),
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
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    line = f"{timestamp},{name},{avg_ms:.1f},{min_ms:.1f},{max_ms:.1f},{iterations}\n"
    with open(results_file, "a") as fh:
        fh.write(line)


def format_ms(ms: float) -> str:
    if ms < 0:
        return "N/A"
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
            print(f"    FAILED (all iterations errored)")
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


def save_baseline(results: list[dict]) -> None:
    measurements = {}
    for r in results:
        if r["error"]:
            continue
        measurements[r["name"]] = {
            "avg_ms": round(r["avg"], 1),
            "max_allowed_ms": round(r["avg"] * REGRESSION_THRESHOLD_PERCENT / 100, 1),
        }

    baseline = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": _get_git_commit(),
        "threshold_percent": REGRESSION_THRESHOLD_PERCENT,
        "measurements": measurements,
    }
    with open(BASELINE_PATH, "w") as f:
        json.dump(baseline, f, indent=2)
        f.write("\n")

    print(f"\nBaseline saved to {BASELINE_PATH}")
    print(f"  Commit: {baseline['git_commit']}")
    print(f"  Threshold: {REGRESSION_THRESHOLD_PERCENT}%")
    for name, data in measurements.items():
        print(
            f"  {name}: {format_ms(data['avg_ms'])} "
            f"(max {format_ms(data['max_allowed_ms'])})"
        )


def check_baseline() -> bool:
    if not BASELINE_PATH.exists():
        print(f"FAIL: No baseline at {BASELINE_PATH.relative_to(DOTFILES_DIRECTORY)}")
        print("  Run 'benchmark-desktop --save-baseline' to generate it.")
        return False

    with open(BASELINE_PATH) as f:
        baseline = json.load(f)

    failures: list[str] = []

    generated_at = datetime.fromisoformat(baseline["generated_at"])
    age_days = (datetime.now(timezone.utc) - generated_at).days
    if age_days > MAXIMUM_BASELINE_AGE_DAYS:
        failures.append(
            f"Baseline is {age_days} days old (max {MAXIMUM_BASELINE_AGE_DAYS}). "
            "Re-run 'benchmark-desktop --save-baseline'."
        )

    measurements = baseline.get("measurements", {})
    if not measurements:
        failures.append("Baseline has no measurements.")

    print("=" * 60)
    print("DESKTOP PERFORMANCE BASELINE CHECK")
    print("=" * 60)
    print(f"  Generated: {baseline['generated_at']}")
    print(f"  Age: {age_days} days")
    print(f"  Commit: {baseline.get('git_commit', 'unknown')}")
    print(f"  Threshold: {baseline.get('threshold_percent', '?')}%")
    for name, data in measurements.items():
        print(
            f"  {name}: {format_ms(data['avg_ms'])} "
            f"(max {format_ms(data['max_allowed_ms'])})"
        )

    if failures:
        print(f"\nFAILED ({len(failures)} issues):")
        for f in failures:
            print(f"  - {f}")
        return False

    print("\nPASSED: Baseline is valid.")
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


def _get_git_commit() -> str:
    result = subprocess.run(
        ["git", "-C", str(DOTFILES_DIRECTORY), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def parse_arguments(argv: list[str]) -> tuple[str, int, str | None]:
    if "--save-baseline" in argv:
        return "save-baseline", DEFAULT_ITERATIONS, None
    if "--check-baseline" in argv:
        return "check-baseline", 0, None

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
    print()
    print("Components (partial match):")
    print("  hyprctl, workspace, switcher, launcher, dashboard,")
    print("  sidebar, overview, volume, fuzzel, fish, wezterm, tmux")
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
    ensure_results_directory_exists()
    initialize_csv_if_needed(results_file)

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
        save_baseline(results)
    else:
        print(f"\nResults saved to {results_file}")


if __name__ == "__main__":
    main()
