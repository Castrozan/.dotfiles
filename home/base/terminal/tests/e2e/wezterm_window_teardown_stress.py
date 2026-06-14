#!/usr/bin/env python3

import argparse
import pathlib
import sys
import tempfile

from isolated_gui import (
    MACOS_OPENGL_SHIM_FRAMEWORK_MARKER,
    gui_process_is_alive,
    gui_socket_path,
    launch_isolated_gui,
    loaded_opengl_shim_framework_count,
    terminate_gui,
    wait_for_gui_socket,
    write_isolated_config,
)
from window_driver import close_window_by_pane, spawn_new_window

MACOS_CRASH_REPORT_DIRECTORY = pathlib.Path.home() / "Library/Logs/DiagnosticReports"


def count_wezterm_crash_reports():
    if not MACOS_CRASH_REPORT_DIRECTORY.is_dir():
        return 0
    return len(list(MACOS_CRASH_REPORT_DIRECTORY.glob("wezterm-gui-*.ips")))


def emit(passed, message):
    print(f"{'PASS' if passed else 'FAIL'}: {message}")
    return passed


def assert_backend(front_end, gui_process_id):
    shim_count = loaded_opengl_shim_framework_count(gui_process_id)
    if front_end == "OpenGL":
        return emit(
            shim_count > 0,
            f"[{front_end}] control: OpenGL shim {MACOS_OPENGL_SHIM_FRAMEWORK_MARKER} is loaded ({shim_count} handles)",
        )
    return emit(
        shim_count == 0,
        f"[{front_end}] renderer is off the OpenGL shim: zero {MACOS_OPENGL_SHIM_FRAMEWORK_MARKER} handles loaded",
    )


def cycle_windows_until_crash(front_end, socket_path, gui_popen, cycles):
    for cycle_index in range(cycles):
        pane_id = spawn_new_window(socket_path)
        if pane_id is None:
            return emit(
                False, f"[{front_end}] failed to open window on cycle {cycle_index}"
            )
        close_window_by_pane(socket_path, pane_id)
        if not gui_process_is_alive(gui_popen):
            return emit(
                False,
                f"[{front_end}] gui crashed during window teardown on cycle {cycle_index} (exit {gui_popen.returncode})",
            )
    return emit(
        True,
        f"[{front_end}] survived {cycles} window open/close teardown cycles with no segfault",
    )


def run_backend_and_teardown_stress(front_end, cycles):
    crash_reports_before = count_wezterm_crash_reports()
    all_passed = True
    with tempfile.TemporaryDirectory(
        prefix="wezterm-teardown-stress-"
    ) as raw_directory:
        config_path = write_isolated_config(pathlib.Path(raw_directory))
        gui_popen = launch_isolated_gui(
            front_end, config_path, f"WeztermTeardownStress{front_end}"
        )
        socket_path = gui_socket_path(gui_popen.pid)
        try:
            if not wait_for_gui_socket(gui_popen.pid, timeout_seconds=20):
                return emit(
                    False, f"[{front_end}] isolated gui never exposed its socket"
                )
            all_passed &= assert_backend(front_end, gui_popen.pid)
            all_passed &= cycle_windows_until_crash(
                front_end, socket_path, gui_popen, cycles
            )
            crash_reports_after = count_wezterm_crash_reports()
            all_passed &= emit(
                crash_reports_after == crash_reports_before,
                f"[{front_end}] no new macOS crash report during the run ({crash_reports_before} before, {crash_reports_after} after)",
            )
        finally:
            terminate_gui(gui_popen)
    return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="Drive an isolated WezTerm GUI through repeated window open/close "
        "teardown cycles and assert it never segfaults, while proving which GPU backend "
        "is active. Reproduces the Cmd-W autorelease-pool teardown crash path."
    )
    parser.add_argument("--front-end", choices=["WebGpu", "OpenGL"], default="WebGpu")
    parser.add_argument("--cycles", type=int, default=100)
    parser.add_argument("--both", action="store_true")
    arguments = parser.parse_args()

    if sys.platform != "darwin":
        print("SKIP: window teardown stress is a macOS GUI test")
        return 0

    if arguments.both:
        opengl_passed = run_backend_and_teardown_stress("OpenGL", arguments.cycles)
        webgpu_passed = run_backend_and_teardown_stress("WebGpu", arguments.cycles)
        passed = opengl_passed and webgpu_passed
    else:
        passed = run_backend_and_teardown_stress(arguments.front_end, arguments.cycles)

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
