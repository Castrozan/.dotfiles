import asyncio
import json
import socket
import stat
import urllib.error
import urllib.request

import pytest
import seat_bridge
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed, InvalidStatus

VOICE = b"\x01\x02" * 480
MICROPHONE = b"\x03\x04" * 320


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
    monkeypatch.setenv("PATH", f"{directory}:/bin:/usr/bin")
    return heard


@pytest.fixture
def bridge(tmp_path, monkeypatch):
    port = free_port()
    monkeypatch.setattr(seat_bridge, "PORT", port)
    monkeypatch.setattr(seat_bridge, "ALLOWED_ORIGINS", [f"http://localhost:{port}"])
    page = tmp_path / "page"
    page.mkdir()
    (page / "index.html").write_text("<p>seat</p>")
    heard = install_fake_audio_tools(tmp_path, monkeypatch)
    return type("Bridge", (), {"port": port, "page": page, "heard": heard})


def run_beside_bridge(bridge, scenario):
    async def run():
        serving = asyncio.create_task(seat_bridge.serve_remote_seat(bridge.page))
        try:
            await wait_until_listening(bridge.port)
            return await scenario()
        finally:
            serving.cancel()
            await asyncio.gather(serving, return_exceptions=True)

    return asyncio.run(run())


async def wait_until_listening(port):
    for _ in range(200):
        try:
            _, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.close()
            await writer.wait_closed()
            return
        except OSError:
            await asyncio.sleep(0.01)
    raise TimeoutError("The bridge never listened")


async def fetch(port, path):
    def read():
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}{path}", timeout=2
            ) as reply:
                return reply.status, reply.read()
        except urllib.error.HTTPError as refusal:
            with refusal:
                return refusal.code, refusal.read()

    return await asyncio.to_thread(read)


def seat_socket(bridge, origin=None):
    return connect(
        f"ws://127.0.0.1:{bridge.port}/audio",
        origin=origin or f"http://localhost:{bridge.port}",
    )


def test_the_page_and_its_health_are_served_and_nothing_else(bridge):
    async def scenario():
        page = await fetch(bridge.port, "/")
        health = await fetch(bridge.port, "/health")
        missing = await fetch(bridge.port, "/listener.json")
        return page, json.loads(health[1]), missing[0]

    page, health, missing = run_beside_bridge(bridge, scenario)
    assert page == (200, b"<p>seat</p>")
    assert health == {"attached": False, "failure": None}
    assert missing == 404


def test_audio_travels_both_ways_while_a_machine_holds_the_seat(bridge):
    async def scenario():
        async with seat_socket(bridge) as socket_to_seat:
            await socket_to_seat.send(MICROPHONE)
            voice = b""
            while len(voice) < len(VOICE):
                voice += await asyncio.wait_for(socket_to_seat.recv(), 5)
            attached = json.loads((await fetch(bridge.port, "/health"))[1])
        released = attached
        for _ in range(200):
            released = json.loads((await fetch(bridge.port, "/health"))[1])
            if not released["attached"]:
                break
            await asyncio.sleep(0.01)
        return voice, attached, released

    voice, attached, released = run_beside_bridge(bridge, scenario)
    assert voice == VOICE
    assert bridge.heard.read_bytes() == MICROPHONE
    assert attached["attached"] is True
    assert released["attached"] is False


def test_a_page_from_another_origin_cannot_reach_the_audio(bridge):
    async def scenario():
        with pytest.raises(InvalidStatus) as refused:
            async with seat_socket(bridge, origin="https://example.com"):
                pass
        return refused.value.response.status_code

    assert run_beside_bridge(bridge, scenario) == 403


def test_a_second_machine_is_refused_while_the_seat_is_held(bridge):
    async def scenario():
        async with seat_socket(bridge) as holder:
            await holder.send(MICROPHONE)
            async with seat_socket(bridge) as intruder:
                with pytest.raises(ConnectionClosed) as refused:
                    await asyncio.wait_for(intruder.recv(), 5)
            return refused.value.rcvd.code

    assert run_beside_bridge(bridge, scenario) == seat_bridge.SEAT_TAKEN_CODE


def test_a_page_failure_shows_in_the_health(bridge):
    async def scenario():
        await fetch(bridge.port, "/failure?NotAllowedError%3A%20denied")
        return json.loads((await fetch(bridge.port, "/health"))[1])

    assert run_beside_bridge(bridge, scenario)["failure"] == "NotAllowedError: denied"


def test_the_bridge_ends_when_no_machine_takes_the_seat(bridge, monkeypatch):
    monkeypatch.setattr(seat_bridge, "FIRST_ATTACH_SECONDS", 0.05)
    asyncio.run(asyncio.wait_for(seat_bridge.serve_remote_seat(bridge.page), 5))


def test_the_bridge_ends_soon_after_its_machine_leaves(bridge, monkeypatch):
    monkeypatch.setattr(seat_bridge, "REATTACH_SECONDS", 0.05)

    async def scenario():
        serving = asyncio.create_task(seat_bridge.serve_remote_seat(bridge.page))
        await wait_until_listening(bridge.port)
        async with seat_socket(bridge) as holder:
            await holder.send(MICROPHONE)
        await asyncio.wait_for(serving, 5)

    asyncio.run(scenario())
