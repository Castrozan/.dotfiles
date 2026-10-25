import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from chrome_consent_dialog import capture_dialog
from chrome_consent_target import (
    consume_token,
    current_target,
    cursor_position,
    focus_window,
    focused_window,
    move_cursor,
    prepare,
    target_signature,
)


def stop_process(process):
    process.terminate()
    try:
        process.wait(timeout=0.5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=0.5)


def interruption(signum, frame):
    raise InterruptedError("Consent attempt ended")


def click_once(configuration, target, button, directory, original_cursor):
    socket = directory / "ydotool.sock"
    process = subprocess.Popen(
        [configuration["ydotoold"], f"--socket-path={socket}", "--socket-perm=0600"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        deadline = time.monotonic() + 1
        while not socket.exists():
            if process.poll() is not None or time.monotonic() >= deadline:
                raise RuntimeError(
                    "Temporary ydotoold could not start; check existing uinput permission"
                )
            time.sleep(0.02)
        if focused_window(configuration) != target["address"]:
            raise RuntimeError("Focus changed before the consent action")
        observed = capture_dialog(configuration, target, directory)
        if observed != button or target_signature(
            current_target(configuration)
        ) != target_signature(target):
            raise RuntimeError(
                "Chrome dialog or process changed before the consent action"
            )
        position = tuple(
            target["at"][index] + button.position[index] for index in (0, 1)
        )
        if cursor_position(configuration) != original_cursor:
            raise RuntimeError("User cursor changed before the consent action")
        move_cursor(configuration, position)
        try:
            if focused_window(configuration) != target["address"]:
                raise RuntimeError("Focus changed after cursor movement")
            subprocess.run(
                [configuration["ydotool"], "click", "0xC0"],
                env={**os.environ, "YDOTOOL_SOCKET": str(socket)},
                check=True,
                capture_output=True,
                timeout=1,
            )
        finally:
            if cursor_position(configuration) == position:
                move_cursor(configuration, original_cursor)
    finally:
        stop_process(process)


def watch(configuration, directory, token, timeout):
    target = consume_token(configuration, directory, token)
    original_focus = focused_window(configuration)
    original_cursor = cursor_position(configuration)
    with tempfile.TemporaryDirectory(prefix="chrome-consent-") as temporary:
        temporary = Path(temporary)
        try:
            focus_window(configuration, target["address"])
            if focused_window(configuration) != target["address"]:
                raise RuntimeError("Chrome could not be focused safely")
            if capture_dialog(configuration, target, temporary) is not None:
                raise RuntimeError(
                    "A consent dialog predates this attempt; refusing to approve it"
                )
            print("ready", flush=True)
            deadline = time.monotonic() + min(timeout, 25)
            while time.monotonic() < deadline:
                if (
                    focused_window(configuration) != target["address"]
                    or cursor_position(configuration) != original_cursor
                ):
                    raise RuntimeError(
                        "User focus or cursor changed during this attempt"
                    )
                if target_signature(current_target(configuration)) != target_signature(
                    target
                ):
                    raise RuntimeError(
                        "Chrome process or geometry changed during this attempt"
                    )
                button = capture_dialog(configuration, target, temporary)
                if button is not None:
                    click_once(
                        configuration, target, button, temporary, original_cursor
                    )
                    return
                time.sleep(0.1)
            raise RuntimeError("No exact consent dialog appeared before the deadline")
        finally:
            if (
                original_focus
                and focused_window(configuration) == target["address"]
                and cursor_position(configuration) == original_cursor
            ):
                focus_window(configuration, original_focus)


def main(arguments):
    os.umask(0o077)
    configuration = json.loads(Path(arguments[0]).read_text())
    operation, directory = arguments[1], Path(arguments[2])
    if operation == "prepare":
        prepare(configuration, directory)
    elif operation == "watch" and len(arguments) == 5:
        watch(configuration, directory, arguments[3], float(arguments[4]))
    else:
        raise ValueError("Expected prepare or one bounded watch invocation")


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, interruption)
    signal.signal(signal.SIGINT, interruption)
    try:
        main(sys.argv[1:])
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"chrome-consent: {error}", file=sys.stderr)
        sys.exit(1)
