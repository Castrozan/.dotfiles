import os
import pathlib
import subprocess
import time

WEZTERM_DATA_DIRECTORY = pathlib.Path.home() / ".local/share/wezterm"
MACOS_OPENGL_SHIM_FRAMEWORK_MARKER = "AppleMetalOpenGLRenderer"

ISOLATED_CONFIG_LUA = """local wezterm = require 'wezterm'
return {
  front_end = os.getenv('WEZTERM_TEARDOWN_STRESS_FRONT_END') or 'WebGpu',
  window_close_confirmation = 'NeverPrompt',
  enable_tab_bar = false,
  initial_cols = 80,
  initial_rows = 24,
}
"""


def write_isolated_config(temporary_directory):
    config_path = temporary_directory / "teardown-stress.lua"
    config_path.write_text(ISOLATED_CONFIG_LUA)
    return config_path


def gui_socket_path(gui_process_id):
    return WEZTERM_DATA_DIRECTORY / f"gui-sock-{gui_process_id}"


def launch_isolated_gui(front_end, config_path, instance_class):
    environment = dict(os.environ)
    environment["WEZTERM_TEARDOWN_STRESS_FRONT_END"] = front_end
    environment["WEZTERM_LOG"] = "error"
    return subprocess.Popen(
        [
            "wezterm",
            "--config-file",
            str(config_path),
            "start",
            "--class",
            instance_class,
            "--always-new-process",
            "--position",
            "screen:80,80",
            "--",
            "sleep",
            "1000000",
        ],
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def wait_for_gui_socket(gui_process_id, timeout_seconds):
    deadline = time.monotonic() + timeout_seconds
    socket_path = gui_socket_path(gui_process_id)
    while time.monotonic() < deadline:
        if socket_path.is_socket():
            return True
        time.sleep(0.25)
    return False


def loaded_opengl_shim_framework_count(gui_process_id):
    listing = subprocess.run(
        ["lsof", "-p", str(gui_process_id)],
        capture_output=True,
        text=True,
    )
    return sum(
        1
        for line in listing.stdout.splitlines()
        if MACOS_OPENGL_SHIM_FRAMEWORK_MARKER in line
    )


def gui_process_is_alive(gui_popen):
    return gui_popen.poll() is None


def terminate_gui(gui_popen):
    if gui_popen.poll() is None:
        gui_popen.terminate()
        try:
            gui_popen.wait(timeout=5)
        except subprocess.TimeoutExpired:
            gui_popen.kill()
