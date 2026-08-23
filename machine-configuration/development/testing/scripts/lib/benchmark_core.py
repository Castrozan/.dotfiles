import os
import subprocess
import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

BENCHMARK_CHECKOUT_VARIABLE = "DOTFILES_BENCHMARK_CHECKOUT"
BENCHMARK_HOST_VARIABLE = "DOTFILES_BENCHMARK_HOST"

DOTFILES_DIRECTORY = Path(
    os.environ.get(BENCHMARK_CHECKOUT_VARIABLE) or Path.home() / ".dotfiles"
)
TRACKED_BASELINE_DIRECTORY = (
    DOTFILES_DIRECTORY / "machine-configuration" / "development" / "testing"
)
RESULTS_DIRECTORY = Path.home() / ".local" / "share" / "dotfiles-benchmarks"


@dataclass(frozen=True)
class CommandMeasurement:
    succeeded: bool
    elapsed_seconds: float


@dataclass(frozen=True)
class BenchmarkTarget:
    host: str
    configuration: str
    flake_output: str


@dataclass(frozen=True)
class ValueAggregate:
    total: float
    count: int


BENCHMARK_TARGETS = {
    "kira": BenchmarkTarget("kira", "darwin", "darwinConfigurations.kira.system"),
    "rin": BenchmarkTarget("rin", "darwin", "darwinConfigurations.rin.system"),
    "chise": BenchmarkTarget(
        "chise",
        "nixos",
        "nixosConfigurations.chise.config.system.build.toplevel",
    ),
}


def configured_benchmark_host() -> str:
    return os.environ.get(BENCHMARK_HOST_VARIABLE, "").strip()


def configured_benchmark_target() -> BenchmarkTarget | None:
    return BENCHMARK_TARGETS.get(configured_benchmark_host())


def required_benchmark_target() -> BenchmarkTarget:
    target = configured_benchmark_target()
    if target is not None:
        return target
    known_hosts = ", ".join(sorted(BENCHMARK_TARGETS))
    print(
        f"{BENCHMARK_HOST_VARIABLE} is "
        f"'{configured_benchmark_host()}', which names no configured host. "
        f"Expected one of {known_hosts}. The nix packaging of this command "
        "injects it from the host alias the flake builds."
    )
    raise SystemExit(1)


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


def latest_value_by_key(
    data_lines: list[str],
    key_columns: tuple[int, ...],
    value_column: int,
) -> dict[str, float]:
    return dict(_keyed_values(data_lines, key_columns, value_column))


def aggregate_values_by_key(
    data_lines: list[str],
    key_columns: tuple[int, ...],
    value_column: int,
) -> dict[str, ValueAggregate]:
    aggregates: dict[str, ValueAggregate] = {}
    for key, value in _keyed_values(data_lines, key_columns, value_column):
        running = aggregates.get(key, ValueAggregate(0.0, 0))
        aggregates[key] = ValueAggregate(running.total + value, running.count + 1)
    return aggregates


def _keyed_values(
    data_lines: list[str],
    key_columns: tuple[int, ...],
    value_column: int,
) -> Iterator[tuple[str, float]]:
    required_field_count = max((*key_columns, value_column)) + 1
    for line in data_lines:
        fields = line.split(",")
        if len(fields) < required_field_count:
            continue
        try:
            value = float(fields[value_column])
        except ValueError:
            continue
        yield ",".join(fields[column] for column in key_columns), value


def recent_result_table_lines(result_lines: list[str], row_limit: int) -> list[str]:
    header = result_lines[0].split(",")
    recent = (
        result_lines[-row_limit:]
        if len(result_lines) > row_limit + 1
        else result_lines[1:]
    )
    rows = [line.split(",") for line in recent]
    column_widths = [len(column) for column in header]
    for fields in rows:
        for index, field in enumerate(fields):
            if index < len(column_widths):
                column_widths[index] = max(column_widths[index], len(field))
    row_format = "  ".join(f"{{:<{width}}}" for width in column_widths)
    return [row_format.format(*row) for row in (header, *rows)]
