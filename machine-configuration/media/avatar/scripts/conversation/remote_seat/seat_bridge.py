import asyncio
import http
import json
import os
import pathlib
import signal
import sys
import urllib.parse

from websockets.asyncio.server import serve
from websockets.datastructures import Headers
from websockets.http11 import Response

HOST = "127.0.0.1"
PORT = 8769
ALLOWED_ORIGINS = [f"http://localhost:{PORT}", f"http://{HOST}:{PORT}"]
AUDIO_PATH = "/audio"
HEALTH_PATH = "/health"
FAILURE_PATH = "/failure"
PAGE_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/seat.js": ("seat.js", "text/javascript"),
    "/seat-audio-worklets.js": ("seat-audio-worklets.js", "text/javascript"),
}
CLIENT_NAME = "avatar-remote-seat"
MICROPHONE_SINK = "AvatarRemoteMicrophone"
MICROPHONE_RATE = 16000
VOICE_SOURCE = "AvatarLipSync.monitor"
VOICE_RATE = 24000
VOICE_CHUNK_BYTES = VOICE_RATE * 2 // 50
FIRST_ATTACH_SECONDS = 30
REATTACH_SECONDS = 10
SEAT_TAKEN_CODE = 1013


def microphone_playback_command():
    return [
        "pacat",
        "--playback",
        f"--device={MICROPHONE_SINK}",
        f"--client-name={CLIENT_NAME}",
        "--raw",
        "--format=s16le",
        f"--rate={MICROPHONE_RATE}",
        "--channels=1",
        "--latency-msec=60",
    ]


def voice_capture_command():
    return [
        "parec",
        f"--device={VOICE_SOURCE}",
        f"--client-name={CLIENT_NAME}",
        "--raw",
        "--format=s16le",
        f"--rate={VOICE_RATE}",
        "--channels=1",
        "--latency-msec=40",
    ]


def body_response(body, content_type):
    headers = Headers(
        [
            ("Content-Type", content_type),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store"),
            ("Connection", "close"),
        ]
    )
    return Response(http.HTTPStatus.OK, "OK", headers, body)


async def relay_microphone(websocket, playback_input):
    async for frame in websocket:
        if isinstance(frame, bytes):
            playback_input.write(frame)
            await playback_input.drain()


async def relay_voice(capture_output, websocket):
    while chunk := await capture_output.read(VOICE_CHUNK_BYTES):
        await websocket.send(chunk)


async def until_first_finishes(*coroutines):
    tasks = [asyncio.create_task(coroutine) for coroutine in coroutines]
    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


async def end_process(process):
    if process.returncode is None:
        process.terminate()
    await process.wait()


class RemoteSeat:
    def __init__(self, page_directory):
        self.page_directory = page_directory
        self.attached = asyncio.Event()
        self.detached = asyncio.Event()
        self.failure = None

    def answer_request(self, connection, request):
        path, _, query = request.path.partition("?")
        if path == AUDIO_PATH:
            return None
        if path == HEALTH_PATH:
            health = {"attached": self.attached.is_set(), "failure": self.failure}
            return body_response(json.dumps(health).encode(), "application/json")
        if path == FAILURE_PATH:
            self.failure = urllib.parse.unquote(query)
            print(f"The seat page failed: {self.failure}", file=sys.stderr)
            return body_response(b"", "text/plain")
        if path in PAGE_FILES:
            name, content_type = PAGE_FILES[path]
            return body_response(
                (self.page_directory / name).read_bytes(), content_type
            )
        return connection.respond(http.HTTPStatus.NOT_FOUND, "")

    async def carry_audio(self, websocket):
        if self.attached.is_set():
            await websocket.close(SEAT_TAKEN_CODE, "Another machine holds the seat")
            return
        self.failure = None
        self.detached.clear()
        self.attached.set()
        microphone = await asyncio.create_subprocess_exec(
            *microphone_playback_command(), stdin=asyncio.subprocess.PIPE
        )
        voice = await asyncio.create_subprocess_exec(
            *voice_capture_command(), stdout=asyncio.subprocess.PIPE
        )
        try:
            await until_first_finishes(
                relay_microphone(websocket, microphone.stdin),
                relay_voice(voice.stdout, websocket),
            )
        finally:
            await end_process(microphone)
            await end_process(voice)
            self.attached.clear()
            self.detached.set()

    async def stay_while_taken(self):
        grace = FIRST_ATTACH_SECONDS
        while True:
            try:
                await asyncio.wait_for(self.attached.wait(), grace)
            except TimeoutError:
                print("No machine holds the remote seat", file=sys.stderr)
                return
            await self.detached.wait()
            grace = REATTACH_SECONDS


async def serve_remote_seat(page_directory):
    seat = RemoteSeat(page_directory)
    stopping = asyncio.Event()
    asyncio.get_running_loop().add_signal_handler(signal.SIGTERM, stopping.set)
    async with serve(
        seat.carry_audio,
        HOST,
        PORT,
        origins=ALLOWED_ORIGINS,
        process_request=seat.answer_request,
    ):
        await until_first_finishes(seat.stay_while_taken(), stopping.wait())


if __name__ == "__main__":
    asyncio.run(serve_remote_seat(pathlib.Path(os.environ["AVATAR_SEAT_PAGE"])))
