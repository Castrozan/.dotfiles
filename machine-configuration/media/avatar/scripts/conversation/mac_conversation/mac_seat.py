import asyncio
import os
import pathlib
import signal
import sys

import local_seat
import mac_microphone
import mac_seat_client
import seat_page
from mac_microphone import MicrophoneRelay

VOICE_RATE = 24000
CHUNK_SECONDS = 0.02
CHUNK_BYTES = int(VOICE_RATE * CHUNK_SECONDS) * 2
LEAD_SECONDS = 0.1
PAGE_CUSHION_SECONDS = 0.15
LONGEST_SPEECH_BYTES = VOICE_RATE * 2 * 600
NO_PAGE_MESSAGE = (
    f"The conversation page did not attach; check that {local_seat.BROWSER} "
    "may use the microphone"
)


class MacSeat(MicrophoneRelay):
    def __init__(self, page_files, output):
        super().__init__(page_files, output)
        self.hushed = asyncio.Event()

    def answer_request(self, connection, request):
        path = request.path.partition("?")[0]
        if path == mac_seat_client.SPEECH_PATH:
            return None
        if path == mac_seat_client.HUSH_PATH:
            self.hushed.set()
            return seat_page.body_response(b"", "text/plain")
        return super().answer_request(connection, request)

    async def carry(self, websocket):
        if websocket.request.path == mac_seat_client.SPEECH_PATH:
            await self.carry_speech(websocket)
            return
        await self.carry_audio(websocket)

    async def carry_speech(self, websocket):
        self.hushed.set()
        hushed = self.hushed = asyncio.Event()
        pcm = await websocket.recv()
        if isinstance(pcm, bytes):
            await self.play(pcm, hushed)

    async def play(self, pcm, hushed):
        clock = asyncio.get_running_loop().time
        started = clock()
        samples = pcm[: len(pcm) - len(pcm) % 2]
        for sent, offset in enumerate(range(0, len(samples), CHUNK_BYTES), start=1):
            if hushed.is_set() or self.page_socket is None:
                return
            await self.page_socket.send(samples[offset : offset + CHUNK_BYTES])
            ahead = started + sent * CHUNK_SECONDS - LEAD_SECONDS - clock()
            await asyncio.sleep(max(0, ahead))
        await asyncio.sleep(LEAD_SECONDS + PAGE_CUSHION_SECONDS)


def open_seat_page():
    mac_seat_client.close_browser()
    local_seat.open_headless_browser(
        mac_seat_client.PROFILE_FLAG,
        mac_seat_client.PORT,
        "--autoplay-policy=no-user-gesture-required",
    )


async def hold_seat(page_files, output, open_page):
    seat = MacSeat(page_files, output)
    await mac_microphone.serve_until_the_page_leaves(
        seat, seat.carry, mac_seat_client.PORT, open_page, max_size=LONGEST_SPEECH_BYTES
    )


def end_on_terminate(signal_number, frame):
    mac_seat_client.close_browser()
    os._exit(0)


def main():
    signal.signal(signal.SIGTERM, end_on_terminate)
    page_files = seat_page.seat_page_files(pathlib.Path(os.environ["AVATAR_SEAT_PAGE"]))
    try:
        asyncio.run(hold_seat(page_files, sys.stdout.buffer, open_seat_page))
    except TimeoutError:
        print(NO_PAGE_MESSAGE, file=sys.stderr)
        sys.exit(1)
    finally:
        mac_seat_client.close_browser()


if __name__ == "__main__":
    main()
