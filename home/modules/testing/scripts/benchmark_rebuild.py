import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

DOTFILES_DIRECTORY = Path.home() / ".dotfiles"
RESULTS_DIRECTORY = Path.home() / ".local" / "share" / "dotfiles-benchmarks"
RESULTS_FILE_NAME = "rebuild-times.csv"
CSV_HEADER = "timestamp,type,config,duration_seconds,commit"

ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"
ANSI_RESET = "\033[0m"


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


def get_flake_output_for_configuration(configuration_type: str) -> str:
    if configuration_type == "nixos":
        return "nixosConfigurations.zanoni.config.system.build.toplevel"
    return 'homeConfigurations."lucas.zanoni@x86_64-linux".activationPackage'


def get_current_git_short_commit() -> str:
    result = subprocess.run(
        ["git", "-C", str(DOTFILES_DIRECTORY), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return "unknown"


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
) -> None:
    commit_hash = get_current_git_short_commit()
    print(f"Benchmarking: {benchmark_type} ({configuration_type})")

    duration = run_benchmark_command(command)
    record_benchmark_result(
        results_file, benchmark_type, configuration_type, duration, commit_hash
    )
    print(f"  Duration: {duration:.2f}s")


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


def print_averages_by_type(data_lines: list[str]) -> None:
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
    print("Usage: benchmark-rebuild [eval|dry-run|build|all|report] [config]")
    print()
    print("Commands:")
    print("  eval     - Benchmark flake evaluation only")
    print("  dry-run  - Benchmark dry-run build")
    print("  build    - Benchmark full build")
    print("  all      - Run eval and dry-run (default)")
    print("  report   - Show benchmark history")
    print()
    print("Configs:")
    print("  home     - Standalone home-manager (lucas.zanoni)")
    print("  nixos    - NixOS configuration (zanoni)")
    print("  auto     - Auto-detect (default)")


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "all"
    configuration_type = sys.argv[2] if len(sys.argv) > 2 else "auto"

    if configuration_type == "auto":
        configuration_type = detect_configuration_type()

    results_file = get_results_file_path()
    ensure_results_directory_exists()
    initialize_csv_if_needed(results_file)

    flake_output = get_flake_output_for_configuration(configuration_type)
    dotfiles = str(DOTFILES_DIRECTORY)

    benchmark_commands = {
        "eval": f"nix flake check {dotfiles} --no-build",
        "dry-run": f"nix build {dotfiles}#{flake_output} --dry-run",
        "build": f"nix build {dotfiles}#{flake_output}",
    }

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
