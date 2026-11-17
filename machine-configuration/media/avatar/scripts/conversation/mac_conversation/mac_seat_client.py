import contextlib
import http.client
import pathlib
import sys

import local_seat

HOST = "127.0.0.1"
PORT = 8772
SPEECH_PATH = "/speech"
HUSH_PATH = "/hush"
ORIGIN = f"http://{HOST}:{PORT}"
SEAT_PROGRAM = pathlib.Path(__file__).with_name("mac_seat.py")
PROFILE = pathlib.Path.home() / ".local/share/avatar/conversation-browser"
PROFILE_FLAG = f"--user-data-dir={PROFILE}"
HUSH_TIMEOUT_SECONDS = 1
SPEECH_OPEN_TIMEOUT_SECONDS = 5


def capture_command(device):
    return [sys.executable, str(SEAT_PROGRAM)]


def attached():
    return bool((local_seat.health(PORT) or {}).get("attached"))


def hush():
    connection = http.client.HTTPConnection(HOST, PORT, timeout=HUSH_TIMEOUT_SECONDS)
    with contextlib.suppress(OSError, http.client.HTTPException):
        connection.request("GET", HUSH_PATH)
        connection.getresponse().read()
    connection.close()


def play(pcm):
    from websockets.sync.client import connect

    with connect(
        f"ws://{HOST}:{PORT}{SPEECH_PATH}",
        origin=ORIGIN,
        open_timeout=SPEECH_OPEN_TIMEOUT_SECONDS,
    ) as seat:
        seat.send(pcm)
        for _ in seat:
            pass


def close_browser():
    local_seat.end_processes_matching(PROFILE_FLAG)
