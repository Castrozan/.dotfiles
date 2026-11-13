import asyncio
import json
import logging
from types import SimpleNamespace

import channel_levels
import host_state
import pytest
import seat_bridge
from websockets.exceptions import ConnectionClosed, InvalidStatus

VOICE = b"\x01\x02" * 480
MICROPHONE = b"\x03\x04" * 320


def sink(name, volume_percent, mute=False):
    return {
        "name": name,
        "mute": mute,
        "volume": {"mono": {"value_percent": f"{volume_percent}%"}},
    }


@pytest.fixture(autouse=True)
def pulse_sinks(monkeypatch):
    sinks = [sink("AvatarMic", 50), sink("AvatarHuman", 100, mute=True)]
    reads = []

    def items(kind):
        reads.append(kind)
        return list(sinks)

    monkeypatch.setattr(channel_levels.pulse_audio, "items", items)
    monkeypatch.setattr(host_state.listener_runtime, "listening", lambda: False)
    monkeypatch.setattr(host_state.user_units, "unit_active", lambda unit: True)
    return SimpleNamespace(sinks=sinks, reads=reads)


async def next_levels(socket_to_seat):
    while True:
        frame = await asyncio.wait_for(socket_to_seat.recv(), 5)
        if isinstance(frame, str):
            return json.loads(frame)


def test_the_page_and_its_health_are_served_and_nothing_else(bridge):
    async def scenario():
        page = await bridge.fetch("/")
        missing = await bridge.fetch("/listener.json")
        return page, await bridge.health(), missing[0]

    page, health, missing = bridge.run_beside(scenario)
    assert page == (200, b"<p>seat</p>")
    assert (health["attached"], health["meeting"]) == (False, True)
    assert missing == 404


def test_audio_travels_both_ways_while_a_machine_holds_the_seat(bridge):
    async def scenario():
        async with bridge.socket() as socket_to_seat:
            await socket_to_seat.send(MICROPHONE)
            voice = b""
            while len(voice) < len(VOICE):
                frame = await asyncio.wait_for(socket_to_seat.recv(), 5)
                voice += frame if isinstance(frame, bytes) else b""
            attached = await bridge.health()
        released = attached
        for _ in range(200):
            released = await bridge.health()
            if not released["attached"]:
                break
            await asyncio.sleep(0.01)
        return voice, attached, released

    voice, attached, released = bridge.run_beside(scenario)
    assert voice == VOICE
    assert bridge.heard.read_bytes() == MICROPHONE
    assert attached["attached"] is True
    assert released["attached"] is False


def test_a_page_from_another_origin_cannot_reach_the_audio(bridge):
    async def scenario():
        with pytest.raises(InvalidStatus) as refused:
            async with bridge.socket(origin="https://example.com"):
                pass
        return refused.value.response.status_code

    assert bridge.run_beside(scenario) == 403


def test_a_second_machine_is_refused_while_the_seat_is_held(bridge):
    async def scenario():
        async with bridge.socket() as holder:
            await holder.send(MICROPHONE)
            async with bridge.socket() as intruder:
                with pytest.raises(ConnectionClosed) as refused:
                    await asyncio.wait_for(intruder.recv(), 5)
            return refused.value.rcvd.code

    assert bridge.run_beside(scenario) == seat_bridge.SEAT_TAKEN_CODE


def test_a_page_failure_shows_in_the_health(bridge):
    async def scenario():
        await bridge.fetch("/failure?NotAllowedError%3A%20denied")
        return await bridge.health()

    assert bridge.run_beside(scenario)["failure"] == "NotAllowedError: denied"


def test_another_site_cannot_report_a_failure(bridge):
    async def scenario():
        refused = await bridge.fetch("/failure?forged", fetch_site="cross-site")
        return refused[0], await bridge.health()

    status, health = bridge.run_beside(scenario)
    assert status == 403
    assert health["failure"] is None


def test_a_seat_whose_audio_tools_cannot_start_is_released(bridge, monkeypatch):
    monkeypatch.setenv("PATH", "/nonexistent")

    async def scenario():
        async with bridge.socket() as holder:
            with pytest.raises(ConnectionClosed):
                await asyncio.wait_for(holder.recv(), 5)
        return await bridge.health()

    assert bridge.run_beside(scenario)["attached"] is False


def test_a_connection_that_sends_nothing_leaves_no_error_in_the_log(bridge, caplog):
    async def scenario():
        await bridge.listening()
        return await bridge.health()

    with caplog.at_level(logging.ERROR, logger="websockets.server"):
        bridge.run_beside(scenario)
    assert caplog.records == []


def test_the_bridge_ends_when_no_machine_takes_the_seat(bridge, monkeypatch):
    monkeypatch.setattr(seat_bridge, "FIRST_ATTACH_SECONDS", 0.05)
    asyncio.run(asyncio.wait_for(bridge.serve(), 5))


def test_the_bridge_ends_soon_after_its_machine_leaves(bridge, monkeypatch):
    monkeypatch.setattr(seat_bridge, "REATTACH_SECONDS", 0.05)

    async def scenario():
        serving = asyncio.create_task(bridge.serve())
        await bridge.listening()
        async with bridge.socket() as holder:
            await holder.send(MICROPHONE)
        await asyncio.wait_for(serving, 5)

    asyncio.run(scenario())


def test_the_levels_arrive_on_attach_and_again_each_time_the_endpoint_is_asked(
    bridge, pulse_sinks
):
    async def scenario():
        async with bridge.socket() as socket_to_seat:
            first = await next_levels(socket_to_seat)
            pulse_sinks.sinks[:] = [sink("AvatarMic", 20), sink("AvatarHuman", 80)]
            answered = await bridge.fetch("/levels")
            return first, answered, await next_levels(socket_to_seat)

    first, answered, second = bridge.run_beside(scenario)
    assert first == {"agent": 0.5, "human": 0.0}
    assert answered == (200, b"")
    assert second == {"agent": 0.2, "human": 0.8}


def test_asking_for_the_levels_with_no_machine_attached_sends_nothing(
    bridge, pulse_sinks
):
    async def scenario():
        answered = await bridge.fetch("/levels")
        await asyncio.sleep(0.05)
        return answered

    assert bridge.run_beside(scenario) == (200, b"")
    assert pulse_sinks.reads == []


def test_another_site_cannot_drive_the_levels(bridge, pulse_sinks):
    async def scenario():
        async with bridge.socket() as socket_to_seat:
            await next_levels(socket_to_seat)
            refused = await bridge.fetch("/levels", fetch_site="cross-site")
            await asyncio.sleep(0.05)
            return refused[0]

    assert bridge.run_beside(scenario) == 403
    assert pulse_sinks.reads == ["sinks"]
