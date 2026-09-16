import pathlib

import benchmark_core


def configuration_label(target: benchmark_core.BenchmarkTarget) -> str:
    return f"{target.host}/{target.configuration}"


def get_benchmark_commands(target: benchmark_core.BenchmarkTarget) -> dict[str, str]:
    dotfiles = str(benchmark_core.DOTFILES_DIRECTORY)
    return {
        "eval": f"nix flake check {dotfiles} --no-build",
        "dry-run": (f"nix build {dotfiles}#{target.flake_output} --dry-run"),
        "build": f"nix build {dotfiles}#{target.flake_output}",
        "rebuild": "rebuild",
    }


def record_benchmark_result(
    results_file: pathlib.Path,
    benchmark_type: str,
    configuration: str,
    duration_seconds: float,
    commit_hash: str,
) -> None:
    benchmark_core.append_result_row(
        results_file,
        [
            benchmark_type,
            configuration,
            f"{duration_seconds:.3f}",
            commit_hash,
        ],
    )


def run_and_record_benchmark(
    benchmark_type: str,
    command: str,
    configuration: str,
    results_file: pathlib.Path,
) -> benchmark_core.CommandMeasurement:
    print(f"Benchmarking: {benchmark_type} ({configuration})")
    measurement = benchmark_core.measure_shell_command(command)

    if not measurement.succeeded:
        print(
            f"  Command failed after {measurement.elapsed_seconds:.2f}s; "
            "no result recorded"
        )
        return measurement

    record_benchmark_result(
        results_file,
        benchmark_type,
        configuration,
        measurement.elapsed_seconds,
        benchmark_core.get_current_git_short_commit(),
    )
    print(f"  Duration: {measurement.elapsed_seconds:.2f}s")
    return measurement
