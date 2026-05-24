import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

RESULTS_DIRECTORY = Path.home() / ".local" / "share" / "dotfiles-benchmarks"
RESULTS_FILE_NAME = "shell-times.csv"
CSV_HEADER = "timestamp,shell,avg_seconds,iterations"

DEFAULT_ITERATIONS = 10
DEFAULT_SHELLS = ["bash", "fish"]


def ensure_results_directory_exists() -> None:
    RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)


def get_results_file_path() -> Path:
    return RESULTS_DIRECTORY / RESULTS_FILE_NAME


def initialize_csv_if_needed(results_file: Path) -> None:
    if not results_file.exists():
        results_file.write_text(CSV_HEADER + "\n")


def is_shell_available(shell_name: str) -> bool:
    return shutil.which(shell_name) is not None


def measure_single_shell_startup(shell_name: str) -> float:
    start_time = time.perf_counter()
    subprocess.run(
        [shell_name, "-i", "-c", "exit"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    end_time = time.perf_counter()
    return end_time - start_time


def benchmark_shell_startup(
    shell_name: str, iterations: int
) -> tuple[float, list[float]]:
    individual_times: list[float] = []

    for _ in range(iterations):
        elapsed = measure_single_shell_startup(shell_name)
        individual_times.append(elapsed)
        print(".", end="", flush=True)

    print()
    average_time = sum(individual_times) / len(individual_times)
    return average_time, individual_times


def record_shell_benchmark_result(
    results_file: Path,
    shell_name: str,
    average_seconds: float,
    iterations: int,
) -> None:
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    line = f"{timestamp},{shell_name},{average_seconds:.6f},{iterations}\n"
    with open(results_file, "a") as file_handle:
        file_handle.write(line)


def format_individual_times(times: list[float]) -> str:
    return " ".join(f"{t:.3f}" for t in times)


def determine_shells_to_benchmark(shell_argument: str | None) -> list[str]:
    if shell_argument is None or shell_argument == "all":
        return DEFAULT_SHELLS.copy()
    return [shell_argument]


def parse_arguments(argv: list[str]) -> tuple[int, list[str]]:
    iterations = DEFAULT_ITERATIONS
    shell_argument = None

    if len(argv) >= 1:
        try:
            iterations = int(argv[0])
        except ValueError:
            print(
                f"Error: Invalid iteration count: {argv[0]}",
                file=sys.stderr,
            )
            raise SystemExit(1)

    if len(argv) >= 2:
        shell_argument = argv[1]

    shells = determine_shells_to_benchmark(shell_argument)
    return iterations, shells


def main() -> None:
    iterations, shells = parse_arguments(sys.argv[1:])

    results_file = get_results_file_path()
    ensure_results_directory_exists()
    initialize_csv_if_needed(results_file)

    print("=== Shell Startup Benchmark ===")
    print()

    for shell_name in shells:
        if not is_shell_available(shell_name):
            print(f"Skipping {shell_name} (not installed)")
            continue

        print(f"Benchmarking {shell_name} startup ({iterations} iterations)...")

        average, individual_times = benchmark_shell_startup(shell_name, iterations)
        record_shell_benchmark_result(results_file, shell_name, average, iterations)

        print(f"  Average: {average:.3f}s")
        print(f"  Individual times: {format_individual_times(individual_times)}")
        print()

    print(f"Results saved to {results_file}")


if __name__ == "__main__":
    main()
