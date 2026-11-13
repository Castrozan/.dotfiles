import asyncio
import http.client
import io
import json
import os
import socket
import stat
from unittest.mock import Mock

import mac_microphone
import pytest
import seat_bridge
from websockets.asyncio.client import connect

VOICE = b"\x01\x02" * 480


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def install_fake_audio_tools(directory, monkeypatch):
    heard = directory / "heard.raw"
    voice = directory / "voice.raw"
    voice.write_bytes(VOICE)
    tools = {
        "pacat": f'#!/bin/sh\nexec cat > "{heard}"\n',
        "parec": f'#!/bin/sh\ncat "{voice}"\nexec sleep 30\n',
    }
    for name, script in tools.items():
        tool = directory / name
        tool.write_text(script)
        tool.chmod(tool.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("PATH", f"{directory}:{os.environ['PATH']}")
    return heard


class BridgeUnderTest:
    def __init__(self, port, page, heard):
        self.port = port
        self.page = page
        self.heard = heard

    def serve(self):
        return seat_bridge.serve_remote_seat(self.page)

    def run_beside(self, scenario):
        async def run():
            serving = asyncio.create_task(self.serve())
            try:
                await self.listening()
                return await scenario()
            finally:
                serving.cancel()
                await asyncio.gather(serving, return_exceptions=True)

        return asyncio.run(run())

    async def listening(self):
        for _ in range(200):
            try:
                _, writer = await asyncio.open_connection("127.0.0.1", self.port)
                writer.close()
                await writer.wait_closed()
                return
            except OSError:
                await asyncio.sleep(0.01)
        raise TimeoutError("The bridge never listened")

    async def fetch(self, path, fetch_site="same-origin"):
        def read():
            connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
            try:
                connection.request("GET", path, headers={"Sec-Fetch-Site": fetch_site})
                reply = connection.getresponse()
                return reply.status, reply.read()
            finally:
                connection.close()

        return await asyncio.to_thread(read)

    async def health(self):
        return json.loads((await self.fetch("/health"))[1])

    def socket(self, origin=None):
        return connect(
            f"ws://127.0.0.1:{self.port}/audio",
            origin=origin or f"http://localhost:{self.port}",
        )


@pytest.fixture
def bridge(tmp_path, monkeypatch):
    port = free_port()
    monkeypatch.setattr(seat_bridge, "PORT", port)
    monkeypatch.setattr(seat_bridge, "ALLOWED_ORIGINS", [f"http://localhost:{port}"])
    page = tmp_path / "page"
    page.mkdir()
    (page / "index.html").write_text("<p>seat</p>")
    return BridgeUnderTest(port, page, install_fake_audio_tools(tmp_path, monkeypatch))


class RecordingOutput(io.BytesIO):
    def __init__(self):
        super().__init__()
        self.flushes = 0

    def flush(self):
        self.flushes += 1


class MicrophoneUnderTest:
    def __init__(self, port, page_files):
        self.port = port
        self.page_files = page_files
        self.output = RecordingOutput()
        self.open_page = Mock()

    def relay(self):
        return mac_microphone.relay_microphone(
            self.page_files, self.output, self.open_page
        )

    def run_beside(self, scenario):
        async def run():
            relaying = asyncio.create_task(self.relay())
            try:
                await self.listening()
                await scenario()
            finally:
                relaying.cancel()
                await asyncio.gather(relaying, return_exceptions=True)

        asyncio.run(run())
        return self.output.getvalue()

    async def listening(self):
        for _ in range(200):
            try:
                _, writer = await asyncio.open_connection("127.0.0.1", self.port)
                writer.close()
                await writer.wait_closed()
                return
            except OSError:
                await asyncio.sleep(0.01)
        raise TimeoutError("The relay never listened")

    async def fetch(self, path):
        def read():
            connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
            try:
                connection.request("GET", path)
                reply = connection.getresponse()
                return reply.status, reply.read()
            finally:
                connection.close()

        return await asyncio.to_thread(read)

    def page(self, origin=None):
        return connect(
            f"ws://127.0.0.1:{self.port}/audio",
            origin=origin or f"http://localhost:{self.port}",
        )


@pytest.fixture
def microphone(tmp_path, monkeypatch):
    port = free_port()
    monkeypatch.setattr(mac_microphone, "PORT", port)
    monkeypatch.setattr(mac_microphone, "ALLOWED_ORIGINS", [f"http://localhost:{port}"])
    wake_page = tmp_path / "wake"
    seat_page = tmp_path / "seat"
    wake_page.mkdir()
    seat_page.mkdir()
    (wake_page / "index.html").write_text("<p>wake</p>")
    (wake_page / "wake-capture.js").write_text("wake")
    (wake_page / "microphone-choice.js").write_text("choice")
    (seat_page / "seat-audio-worklets.js").write_text("worklets")
    return MicrophoneUnderTest(
        port, mac_microphone.microphone_page_files(wake_page, seat_page)
    )
