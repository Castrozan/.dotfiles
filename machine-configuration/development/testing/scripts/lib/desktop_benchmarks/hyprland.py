import json
import shutil
import subprocess

import benchmark_core
import desktop_benchmarks.measurement

QUICKSHELL_SETTLE_SECONDS = 0.15


WINDOW_SWITCHER_SETTLE_SECONDS = 0.1


QS_BAR_PATH = str(benchmark_core.DOTFILES_DIRECTORY / ".config" / "quickshell" / "bar")


def quickshell_bar_call(target: str, action: str) -> list[str]:
    return ["qs", "-p", QS_BAR_PATH, "ipc", "call", target, action]


def quickshell_config_call(
    configuration: str,
    target: str,
    action: str,
) -> list[str]:
    return ["qs", "-c", configuration, "ipc", "call", target, action]


def bench_hyprctl_ipc() -> benchmark_core.CommandMeasurement:
    return benchmark_core.measure_command(
        ["hyprctl", "version"],
        timeout_seconds=desktop_benchmarks.measurement.DEFAULT_COMMAND_TIMEOUT_SECONDS,
    )


def bench_hyprctl_clients() -> benchmark_core.CommandMeasurement:
    return benchmark_core.measure_command(
        ["hyprctl", "clients", "-j"],
        timeout_seconds=desktop_benchmarks.measurement.DEFAULT_COMMAND_TIMEOUT_SECONDS,
    )


def bench_workspace_switch() -> benchmark_core.CommandMeasurement:
    active_workspace = subprocess.run(
        ["hyprctl", "activeworkspace", "-j"],
        capture_output=True,
        text=True,
    )
    if active_workspace.returncode != 0:
        return benchmark_core.unmeasurable_command()

    current = json.loads(active_workspace.stdout)["id"]
    target = current + 1 if current < 10 else current - 1
    measurement = benchmark_core.measure_command(
        ["hyprctl", "dispatch", "workspace", str(target)],
        timeout_seconds=desktop_benchmarks.measurement.DEFAULT_COMMAND_TIMEOUT_SECONDS,
    )
    desktop_benchmarks.measurement.run_cleanup_command(
        ["hyprctl", "dispatch", "workspace", str(current)], None
    )
    return measurement


def bench_window_switcher() -> benchmark_core.CommandMeasurement:
    return desktop_benchmarks.measurement.measure_quickshell_toggle(
        quickshell_config_call("switcher", "switcher", "open"),
        quickshell_config_call("switcher", "switcher", "cancel"),
        WINDOW_SWITCHER_SETTLE_SECONDS,
    )


def bench_launcher_qs() -> benchmark_core.CommandMeasurement:
    return desktop_benchmarks.measurement.measure_quickshell_toggle(
        quickshell_bar_call("launcher", "toggle"),
        quickshell_bar_call("launcher", "toggle"),
        QUICKSHELL_SETTLE_SECONDS,
    )


def bench_dashboard() -> benchmark_core.CommandMeasurement:
    return desktop_benchmarks.measurement.measure_quickshell_toggle(
        quickshell_bar_call("dashboard", "toggle"),
        quickshell_bar_call("dashboard", "toggle"),
        QUICKSHELL_SETTLE_SECONDS,
    )


def bench_sidebar() -> benchmark_core.CommandMeasurement:
    return desktop_benchmarks.measurement.measure_quickshell_toggle(
        quickshell_bar_call("sidebar", "toggle"),
        quickshell_bar_call("sidebar", "toggle"),
        QUICKSHELL_SETTLE_SECONDS,
    )


def bench_workspace_overview() -> benchmark_core.CommandMeasurement:
    return desktop_benchmarks.measurement.measure_quickshell_toggle(
        quickshell_config_call("overview", "overview", "toggle"),
        quickshell_config_call("overview", "overview", "toggle"),
        QUICKSHELL_SETTLE_SECONDS,
    )


def bench_volume_control() -> benchmark_core.CommandMeasurement:
    measurement = benchmark_core.measure_command(
        ["volume", "--inc"],
        timeout_seconds=desktop_benchmarks.measurement.DEFAULT_COMMAND_TIMEOUT_SECONDS,
    )
    desktop_benchmarks.measurement.run_cleanup_command(["volume", "--dec"], None)
    return measurement


def bench_fuzzel_launch() -> benchmark_core.CommandMeasurement:
    if not shutil.which("fuzzel"):
        return benchmark_core.unmeasurable_command()
    return desktop_benchmarks.measurement.measure_process_launch(["fuzzel"], 0.3, 3)
