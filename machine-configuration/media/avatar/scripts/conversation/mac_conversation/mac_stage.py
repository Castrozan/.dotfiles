import contextlib
import socket
import subprocess
import time

import listener_session
import local_seat
import local_window
import user_units

STAGE_UNITS = ("avatar-control-server.service", "avatar-renderer.service")
READY_WAIT_SECONDS = 15
POLL_SECONDS = 0.1
SPEECH_TIMEOUT_SECONDS = 310
COMMAND_TIMEOUT_SECONDS = 30
SPEAKERS = "speakers"
RENDERER_PAGE = ""
WINDOW_POLL_SECONDS = 0.5
NOT_READY = "The avatar control server on this Mac did not start"


def answers(port):
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


def standing_already():
    return all(user_units.unit_active(unit) for unit in STAGE_UNITS)


def set_up():
    for unit in STAGE_UNITS:
        if not user_units.unit_active(unit):
            listener_session.start_unit(unit)
    deadline = time.monotonic() + READY_WAIT_SECONDS
    while not answers(local_seat.CONTROL_PORT):
        if time.monotonic() > deadline:
            raise TimeoutError(NOT_READY)
        time.sleep(POLL_SECONDS)


def strike():
    local_window.hide()
    for unit in STAGE_UNITS:
        if user_units.unit_active(unit):
            listener_session.stop_unit(unit)


@contextlib.contextmanager
def standing():
    stood = standing_already()
    set_up()
    try:
        yield
    finally:
        if not stood:
            strike()


def command(*arguments, timeout=COMMAND_TIMEOUT_SECONDS):
    subprocess.run(
        ["avatar-command", *arguments],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
        timeout=timeout,
    )


def speak(text, emotion, voice):
    chosen = [voice] if voice else []
    command("speak", text, emotion, SPEAKERS, *chosen, timeout=SPEECH_TIMEOUT_SECONDS)


def show_character(character):
    if character:
        command("character", character)


def present(shown):
    command("presence", "shown" if shown else "hidden")


def present_once_the_window_renders():
    deadline = time.monotonic() + READY_WAIT_SECONDS
    while True:
        try:
            present(True)
            return
        except subprocess.CalledProcessError:
            if time.monotonic() > deadline:
                raise
            time.sleep(WINDOW_POLL_SECONDS)


def show_window():
    local_window.hide()
    local_window.open_window(RENDERER_PAGE, local_seat.RENDERER_PORT)
    present_once_the_window_renders()


def hide_window():
    local_window.hide()
