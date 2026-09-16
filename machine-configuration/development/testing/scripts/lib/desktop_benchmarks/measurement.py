import subprocess
import time

import benchmark_core

DEFAULT_COMMAND_TIMEOUT_SECONDS = 10.0


QUICKSHELL_TIMEOUT_SECONDS = 5.0


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
            measurement = benchmark_core.unmeasurable_command()
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


def measure_quickshell_toggle(
    open_arguments: list[str],
    close_arguments: list[str],
    settle_seconds: float,
) -> benchmark_core.CommandMeasurement:
    measurement = benchmark_core.measure_command(
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
) -> benchmark_core.CommandMeasurement:
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
    return benchmark_core.CommandMeasurement(
        succeeded=early_exit_status in (None, 0),
        elapsed_seconds=elapsed_seconds,
    )
