import time

import benchmark_core
import desktop_benchmarks.measurement


def bench_wezterm_launch() -> benchmark_core.CommandMeasurement:
    measurement = desktop_benchmarks.measurement.measure_process_launch(
        ["wezterm", "start", "--", "sleep", "0.5"],
        1.5,
        5,
    )
    time.sleep(0.3)
    return measurement


def bench_tmux_new_session() -> benchmark_core.CommandMeasurement:
    session_name = "_bench_perf_test"
    measurement = benchmark_core.measure_command(
        ["tmux", "new-session", "-d", "-s", session_name],
        timeout_seconds=desktop_benchmarks.measurement.QUICKSHELL_TIMEOUT_SECONDS,
    )
    desktop_benchmarks.measurement.run_cleanup_command(
        ["tmux", "kill-session", "-t", session_name], None
    )
    return measurement


def bench_tmux_split() -> benchmark_core.CommandMeasurement:
    session_name = "_bench_perf_split"
    started = benchmark_core.measure_command(
        ["tmux", "new-session", "-d", "-s", session_name],
        timeout_seconds=desktop_benchmarks.measurement.QUICKSHELL_TIMEOUT_SECONDS,
    )
    if not started.succeeded:
        return benchmark_core.unmeasurable_command()

    measurement = benchmark_core.measure_command(
        ["tmux", "split-window", "-t", session_name],
        timeout_seconds=desktop_benchmarks.measurement.QUICKSHELL_TIMEOUT_SECONDS,
    )
    desktop_benchmarks.measurement.run_cleanup_command(
        ["tmux", "kill-session", "-t", session_name], None
    )
    return measurement
