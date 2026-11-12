import asyncio
import http.client
import json
import os
import socket
import stat

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
