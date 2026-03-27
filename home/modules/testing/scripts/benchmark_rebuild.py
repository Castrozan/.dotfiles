import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

DOTFILES_DIRECTORY = Path.home() / ".dotfiles"
BASELINE_PATH = DOTFILES_DIRECTORY / "home" / "modules" / "testing" / "baseline.json"
RESULTS_DIRECTORY = Path.home() / ".local" / "share" / "dotfiles-benchmarks"
RESULTS_FILE_NAME = "rebuild-times.csv"
CSV_HEADER = "timestamp,type,config,duration_seconds,commit"

MAXIMUM_BASELINE_AGE_DAYS = 30
REGRESSION_THRESHOLD_PERCENT = 150


def ensure_results_directory_exists() -> None:
    RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)


def get_results_file_path() -> Path:
    return RESULTS_DIRECTORY / RESULTS_FILE_NAME


def initialize_csv_if_needed(results_file: Path) -> None:
    if not results_file.exists():
        results_file.write_text(CSV_HEADER + "\n")


def detect_configuration_type() -> str:
    try:
        hostname = Path("/etc/hostname").read_text().strip()
        if Path("/etc/nixos").is_dir() and "zanoni" in hostname:
            return "nixos"
    except (FileNotFoundError, PermissionError):
        pass
    return "home"


def get_flake_output_for_configuration(
    configuration_type: str,
) -> str:
    if configuration_type == "nixos":
        return "nixosConfigurations.zanoni.config.system.build.toplevel"
    return 'homeConfigurations."lucas.zanoni@x86_64-linux".activationPackage'


def get_current_git_short_commit() -> str:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(DOTFILES_DIRECTORY),
            "rev-parse",
            "--short",
            "HEAD",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return "unknown"


def get_benchmark_commands(
    configuration_type: str,
) -> dict[str, str]:
    flake_output = get_flake_output_for_configuration(configuration_type)
    dotfiles = str(DOTFILES_DIRECTORY)
    return {
        "eval": f"nix flake check {dotfiles} --no-build",
        "dry-run": (f"nix build {dotfiles}#{flake_output} --dry-run"),
        "build": f"nix build {dotfiles}#{flake_output}",
        "rebuild": "rebuild",
    }


def run_benchmark_command(command: str) -> float:
    start_time = time.monotonic()
    subprocess.run(
        command,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    end_time = time.monotonic()
    return end_time - start_time


def record_benchmark_result(
    results_file: Path,
    benchmark_type: str,
    configuration_type: str,
    duration_seconds: float,
    commit_hash: str,
) -> None:
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    line = (
        f"{timestamp},{benchmark_type},{configuration_type},"
        f"{duration_seconds:.3f},{commit_hash}\n"
    )
    with open(results_file, "a") as file_handle:
        file_handle.write(line)


def run_and_record_benchmark(
    benchmark_type: str,
    command: str,
    configuration_type: str,
    results_file: Path,
) -> float:
    commit_hash = get_current_git_short_commit()
    print(f"Benchmarking: {benchmark_type} ({configuration_type})")
    duration = run_benchmark_command(command)
    record_benchmark_result(
        results_file,
        benchmark_type,
        configuration_type,
        duration,
        commit_hash,
    )
    print(f"  Duration: {duration:.2f}s")
    return duration


def build_baseline_from_measurements(
    measurements: dict[str, float],
    configuration_type: str,
) -> dict:
    commit_hash = get_current_git_short_commit()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": commit_hash,
        "config": configuration_type,
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
    configuration_type: str,
    results_file: Path,
) -> None:
    measurements: dict[str, float] = {}
    for benchmark_type in ("eval", "rebuild"):
        duration = run_and_record_benchmark(
            benchmark_type,
            benchmark_commands[benchmark_type],
            configuration_type,
            results_file,
        )
        measurements[benchmark_type] = duration

    baseline = build_baseline_from_measurements(measurements, configuration_type)
    with open(BASELINE_PATH, "w") as f:
        json.dump(baseline, f, indent=2)
        f.write("\n")

    print(f"\nBaseline saved to {BASELINE_PATH}")
    print(f"  Commit: {baseline['git_commit']}")
    print(f"  Threshold: {REGRESSION_THRESHOLD_PERCENT}% of measured values")
    for name, data in baseline["measurements"].items():
        print(
            f"  {name}: {data['duration_seconds']:.1f}s "
            f"(max {data['max_allowed_seconds']:.1f}s)"
        )


def check_baseline() -> bool:
    if not BASELINE_PATH.exists():
        print(
            "FAIL: No baseline file found at "
            f"{BASELINE_PATH.relative_to(DOTFILES_DIRECTORY)}"
        )
        print("  Run 'benchmark-rebuild --save-baseline' locally to generate it.")
        return False

    with open(BASELINE_PATH) as f:
        baseline = json.load(f)

    failures: list[str] = []

    generated_at = datetime.fromisoformat(baseline["generated_at"])
    age_days = (datetime.now(timezone.utc) - generated_at).days
    if age_days > MAXIMUM_BASELINE_AGE_DAYS:
        failures.append(
            f"Baseline is {age_days} days old "
            f"(max {MAXIMUM_BASELINE_AGE_DAYS}). "
            f"Re-run 'benchmark-rebuild --save-baseline'."
        )

    measurements = baseline.get("measurements", {})
    if not measurements:
        failures.append("Baseline has no measurements.")

    for name, data in measurements.items():
        max_allowed = data.get("max_allowed_seconds", 0)
        if max_allowed <= 0:
            failures.append(f"{name}: invalid max_allowed_seconds")

    print("=" * 60)
    print("REBUILD PERFORMANCE BASELINE CHECK")
    print("=" * 60)
    print(f"  Generated: {baseline['generated_at']}")
    print(f"  Age: {age_days} days")
    print(f"  Commit: {baseline.get('git_commit', 'unknown')}")
    print(f"  Threshold: {baseline.get('threshold_percent', '?')}%")
    for name, data in measurements.items():
        print(
            f"  {name}: {data['duration_seconds']:.1f}s "
            f"(max {data['max_allowed_seconds']:.1f}s)"
        )

    if failures:
        print(f"\nFAILED ({len(failures)} issues):")
        for failure in failures:
            print(f"  - {failure}")
        return False

    print("\nPASSED: Baseline meets all thresholds.")
    return True


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
    print("Usage: benchmark-rebuild <command> [config]")
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
    print("Configs:")
    print("  home   - Standalone home-manager")
    print("  nixos  - NixOS configuration")
    print("  auto   - Auto-detect (default)")


def main() -> None:
    if "--save-baseline" in sys.argv:
        configuration_type = "auto"
        for arg in sys.argv[1:]:
            if arg != "--save-baseline":
                configuration_type = arg
                break
        if configuration_type == "auto":
            configuration_type = detect_configuration_type()
        results_file = get_results_file_path()
        ensure_results_directory_exists()
        initialize_csv_if_needed(results_file)
        benchmark_commands = get_benchmark_commands(configuration_type)
        save_baseline(
            benchmark_commands,
            configuration_type,
            results_file,
        )
        return

    if "--check-baseline" in sys.argv:
        passed = check_baseline()
        raise SystemExit(0 if passed else 1)

    command = sys.argv[1] if len(sys.argv) > 1 else "all"
    configuration_type = sys.argv[2] if len(sys.argv) > 2 else "auto"

    if configuration_type == "auto":
        configuration_type = detect_configuration_type()

    results_file = get_results_file_path()
    ensure_results_directory_exists()
    initialize_csv_if_needed(results_file)

    benchmark_commands = get_benchmark_commands(configuration_type)

    if command == "report":
        print_recent_results(results_file)
    elif command == "all":
        for benchmark_type in ("eval", "dry-run"):
            run_and_record_benchmark(
                benchmark_type,
                benchmark_commands[benchmark_type],
                configuration_type,
                results_file,
            )
    elif command in benchmark_commands:
        run_and_record_benchmark(
            command,
            benchmark_commands[command],
            configuration_type,
            results_file,
        )
    else:
        print_usage()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
