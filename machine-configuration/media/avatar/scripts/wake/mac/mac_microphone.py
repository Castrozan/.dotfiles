import asyncio
import logging
import os
import pathlib
import signal
import sys

import local_seat
import seat_page
from seat_page import SeatPage
from websockets.asyncio.server import serve

HOST = "127.0.0.1"
PORT = 8771


def allowed_origins(port):
    return [f"http://localhost:{port}", f"http://{HOST}:{port}"]


ALLOWED_ORIGINS = allowed_origins(PORT)
AUDIO_PATH = "/audio"
PAGE_TAKEN_CODE = 1013
ATTACH_SECONDS = 30
WAKE_PROFILE = pathlib.Path.home() / ".local/share/avatar/wake-browser"
WAKE_PROFILE_FLAG = f"--user-data-dir={WAKE_PROFILE}"
NO_PAGE_MESSAGE = (
    f"The wake microphone page did not attach; check that {local_seat.BROWSER} "
    "may use the microphone"
)


def microphone_page_files(wake_page, seat_audio_page):
    return {
        "/": (wake_page / "index.html", seat_page.HTML),
        "/wake-capture.js": (wake_page / "wake-capture.js", seat_page.JAVASCRIPT),
        "/seat-microphone.js": (
            seat_audio_page / "seat-microphone.js",
            seat_page.JAVASCRIPT,
        ),
        "/microphone-choice.js": (
            seat_audio_page / "microphone-choice.js",
            seat_page.JAVASCRIPT,
        ),
        "/seat-audio-worklets.js": (
            seat_audio_page / "seat-audio-worklets.js",
            seat_page.JAVASCRIPT,
        ),
    }


def open_microphone_page():
    local_seat.end_processes_matching(WAKE_PROFILE_FLAG)
    local_seat.open_headless_browser(WAKE_PROFILE_FLAG, PORT)


class MicrophoneRelay:
    def __init__(self, page_files, output):
        self.output = output
        self.attached = asyncio.Event()
        self.detached = asyncio.Event()
        self.page_socket = None
        self.page = SeatPage(page_files, self.attached.is_set)

    def answer_request(self, connection, request):
        if request.path == AUDIO_PATH:
            return None
        return self.page.answer(connection, request)

    async def carry_audio(self, websocket):
        if self.attached.is_set():
            await websocket.close(PAGE_TAKEN_CODE, "Another page holds the microphone")
            return
        self.attached.set()
        self.page_socket = websocket
        try:
            async for frame in websocket:
                if isinstance(frame, bytes):
                    self.output.write(frame)
                    self.output.flush()
        finally:
            self.page_socket = None
            self.detached.set()


async def serve_until_the_page_leaves(relay, carry, port, open_page, **limits):
    logging.getLogger("websockets.server").addFilter(seat_page.sent_a_request)
    async with serve(
        carry,
        HOST,
        port,
        origins=allowed_origins(port),
        process_request=relay.answer_request,
        **limits,
    ):
        open_page()
        await asyncio.wait_for(relay.attached.wait(), ATTACH_SECONDS)
        await relay.detached.wait()


async def relay_microphone(page_files, output, open_page):
    relay = MicrophoneRelay(page_files, output)
    await serve_until_the_page_leaves(relay, relay.carry_audio, PORT, open_page)


def end_on_terminate(signal_number, frame):
    local_seat.end_processes_matching(WAKE_PROFILE_FLAG)
    os._exit(0)


def main():
    signal.signal(signal.SIGTERM, end_on_terminate)
    page_files = microphone_page_files(
        pathlib.Path(os.environ["AVATAR_WAKE_PAGE"]),
        pathlib.Path(os.environ["AVATAR_SEAT_PAGE"]),
    )
    try:
        asyncio.run(
            relay_microphone(page_files, sys.stdout.buffer, open_microphone_page)
        )
    except TimeoutError:
        print(NO_PAGE_MESSAGE, file=sys.stderr)
        sys.exit(1)
    finally:
        local_seat.end_processes_matching(WAKE_PROFILE_FLAG)


if __name__ == "__main__":
    main()
