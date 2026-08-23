import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DOTFILES_DIRECTORY = Path.home() / ".dotfiles"
TRACKED_BASELINE_DIRECTORY = (
    DOTFILES_DIRECTORY / "machine-configuration" / "development" / "testing"
)
RESULTS_DIRECTORY = Path.home() / ".local" / "share" / "dotfiles-benchmarks"


@dataclass(frozen=True)
class CommandMeasurement:
    succeeded: bool
    elapsed_seconds: float


def unmeasurable_command() -> CommandMeasurement:
    return CommandMeasurement(succeeded=False, elapsed_seconds=0.0)


def measure_command(
    arguments: list[str],
    timeout_seconds: float | None = None,
) -> CommandMeasurement:
    return _measure_subprocess(arguments, False, timeout_seconds)


def measure_shell_command(
    command_line: str,
    timeout_seconds: float | None = None,
) -> CommandMeasurement:
    return _measure_subprocess(command_line, True, timeout_seconds)


def _measure_subprocess(
    command: str | list[str],
    use_shell: bool,
    timeout_seconds: float | None,
) -> CommandMeasurement:
    start_time = time.perf_counter()
    try:
        completed_process = subprocess.run(
            command,
            shell=use_shell,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout_seconds,
        )
    except (subprocess.TimeoutExpired, OSError):
        return CommandMeasurement(False, time.perf_counter() - start_time)
    return CommandMeasurement(
        completed_process.returncode == 0,
        time.perf_counter() - start_time,
    )


def get_current_git_short_commit() -> str:
    result = subprocess.run(
        ["git", "-C", str(DOTFILES_DIRECTORY), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return "unknown"


def utc_baseline_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def local_result_timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_results_file_exists(results_file: Path, csv_header: str) -> None:
    results_file.parent.mkdir(parents=True, exist_ok=True)
    if not results_file.exists():
        results_file.write_text(csv_header + "\n")


def append_result_row(results_file: Path, fields: list[str]) -> None:
    row = ",".join([local_result_timestamp(), *fields])
    with open(results_file, "a") as file_handle:
        file_handle.write(row + "\n")
