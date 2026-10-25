import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

from chrome_consent_dialog import capture_dialog
from chrome_consent_input import click_once
from chrome_consent_geometry import clamp_cursor, settle_focused_target
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


def interruption(signum, frame):
    raise InterruptedError("Consent attempt ended")


@contextmanager
def focused_view(configuration, target, deadline):
    original_focus = focused_window(configuration)
    original_cursor = cursor_position(configuration)
    parked_cursor = original_cursor
    try:
        focus_window(configuration, target["address"])
        target, rectangle = settle_focused_target(
            configuration, target, original_cursor, deadline
        )
        if (
            focused_window(configuration) != target["address"]
            or cursor_position(configuration) != original_cursor
        ):
            raise RuntimeError("User focus or cursor changed before parking")
        parked_cursor = clamp_cursor(
            (target["at"][0] + 40, target["at"][1] + 20), rectangle
        )
        move_cursor(configuration, parked_cursor)
        verify_unchanged_attempt(configuration, target, parked_cursor)
        yield target, parked_cursor
    finally:
        restore_view(
            configuration, target, parked_cursor, original_cursor, original_focus
        )


def prepare_watch(configuration, target, temporary, parked_cursor):
    verify_unchanged_attempt(configuration, target, parked_cursor)
    if capture_dialog(configuration, target, temporary) is not None:
        raise RuntimeError(
            "A consent dialog predates this attempt; refusing to approve it"
        )


def verify_unchanged_attempt(configuration, target, parked_cursor):
    if (
        focused_window(configuration) != target["address"]
        or cursor_position(configuration) != parked_cursor
    ):
        raise RuntimeError("User focus or cursor changed during this attempt")
    if target_signature(current_target(configuration)) != target_signature(target):
        raise RuntimeError("Chrome process or geometry changed during this attempt")


def await_consent(configuration, target, temporary, parked_cursor, deadline):
    while time.monotonic() < deadline:
        verify_unchanged_attempt(configuration, target, parked_cursor)
        button = capture_dialog(configuration, target, temporary)
        if button is not None:
            click_once(configuration, target, button, temporary, parked_cursor)
            return
        time.sleep(0.1)
    raise RuntimeError("No exact consent dialog appeared before the deadline")


def restore_view(configuration, target, parked_cursor, original_cursor, original_focus):
    if (
        focused_window(configuration) != target["address"]
        or cursor_position(configuration) != parked_cursor
    ):
        return
    if original_focus:
        focus_window(configuration, original_focus)
    if cursor_position(configuration) == parked_cursor:
        move_cursor(configuration, original_cursor)


def dismiss_failed_attempt(configuration, target, temporary, parked_cursor):
    try:
        verify_unchanged_attempt(configuration, target, parked_cursor)
        if capture_dialog(configuration, target, temporary) is None:
            return
        verify_unchanged_attempt(configuration, target, parked_cursor)
        subprocess.run(
            [configuration["wtype"], "-k", "Escape"],
            check=True,
            capture_output=True,
            timeout=1,
        )
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(
            f"chrome-consent: Could not dismiss own pending dialog: {error}",
            file=sys.stderr,
        )


def watch(configuration, directory, token, timeout):
    deadline = time.monotonic() + min(timeout, 25)
    target = consume_token(configuration, directory, token)
    with tempfile.TemporaryDirectory(prefix="chrome-consent-") as temporary:
        temporary = Path(temporary)
        with focused_view(configuration, target, deadline) as (target, parked_cursor):
            armed = False
            try:
                prepare_watch(configuration, target, temporary, parked_cursor)
                armed = True
                print("ready", flush=True)
                await_consent(configuration, target, temporary, parked_cursor, deadline)
            except BaseException:
                if armed:
                    dismiss_failed_attempt(
                        configuration, target, temporary, parked_cursor
                    )
                raise


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
