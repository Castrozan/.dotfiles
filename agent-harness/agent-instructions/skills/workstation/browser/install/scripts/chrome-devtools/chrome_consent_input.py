import os
import subprocess
import time
from contextlib import contextmanager

from chrome_consent_dialog import capture_dialog
from chrome_consent_target import (
    current_target,
    cursor_position,
    focused_window,
    move_cursor,
    target_signature,
)


def stop_process(process):
    process.terminate()
    try:
        process.wait(timeout=0.5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=0.5)


def require_chrome_focus(configuration, target, message):
    if focused_window(configuration) != target["address"]:
        raise RuntimeError(message)


def await_input_socket(process, socket):
    deadline = time.monotonic() + 1
    while not socket.exists():
        if process.poll() is not None or time.monotonic() >= deadline:
            raise RuntimeError(
                "Temporary ydotoold could not start; check existing uinput permission"
            )
        time.sleep(0.02)


@contextmanager
def temporary_input(configuration, directory):
    socket = directory / "ydotool.sock"
    process = subprocess.Popen(
        [configuration["ydotoold"], f"--socket-path={socket}", "--socket-perm=0600"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        await_input_socket(process, socket)
        yield socket
    finally:
        stop_process(process)


def verify_click_target(configuration, target, button, directory):
    require_chrome_focus(
        configuration, target, "Focus changed before the consent action"
    )
    observed = capture_dialog(configuration, target, directory)
    if observed != button or target_signature(
        current_target(configuration)
    ) != target_signature(target):
        raise RuntimeError("Chrome dialog or process changed before the consent action")


def restore_cursor(configuration, expected_cursor, original_cursor):
    if cursor_position(configuration) == expected_cursor:
        move_cursor(configuration, original_cursor)


def click_once(configuration, target, button, directory, original_cursor):
    with temporary_input(configuration, directory) as socket:
        verify_click_target(configuration, target, button, directory)
        position = tuple(
            target["at"][index] + button.position[index] for index in (0, 1)
        )
        if cursor_position(configuration) != original_cursor:
            raise RuntimeError("User cursor changed before the consent action")
        move_cursor(configuration, position)
        try:
            require_chrome_focus(
                configuration, target, "Focus changed after cursor movement"
            )
            subprocess.run(
                [configuration["ydotool"], "click", "0xC0"],
                env={**os.environ, "YDOTOOL_SOCKET": str(socket)},
                check=True,
                capture_output=True,
                timeout=1,
            )
        finally:
            restore_cursor(configuration, position, original_cursor)
