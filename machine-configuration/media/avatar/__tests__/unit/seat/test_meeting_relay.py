import asyncio
import os

import meeting_relay
import pytest
import seat_bridge
import seat_page
from websockets.exceptions import ConnectionClosed, InvalidStatus

CALL = b"\x05\x06" * 320
MICROPHONE = b"\x03\x04" * 320


async def written(path, length):
    for _ in range(500):
        if path.exists() and len(path.read_bytes()) >= length:
            return path.read_bytes()
        await asyncio.sleep(0.01)
    raise TimeoutError(f"{path} never received {length} bytes")


def test_the_call_plays_into_the_meeting_sink_in_the_microphone_format():
    command = meeting_relay.meeting_playback_command()
    assert command[:2] == ["pacat", "--playback"]
    assert "--device=AvatarRemoteMeeting" in command
    assert "--rate=16000" in command
    assert "--format=s16le" in command
    assert "--channels=1" in command


def test_call_audio_reaches_the_meeting_sink_and_not_the_microphone_sink(bridge):
    async def scenario():
        async with bridge.meeting_socket() as meeting:
            await meeting.send(CALL)
            return await written(bridge.meeting_heard, len(CALL))

    assert bridge.run_beside(scenario) == CALL
    assert not bridge.heard.exists()


def test_a_meeting_socket_does_not_hold_the_seat(bridge):
    async def scenario():
        async with bridge.meeting_socket() as meeting:
            await meeting.send(CALL)
            await written(bridge.meeting_heard, len(CALL))
            during_meeting = await bridge.health()
            async with bridge.socket() as seat:
                await seat.send(MICROPHONE)
                await written(bridge.heard, len(MICROPHONE))
                seated = await bridge.health()
        return during_meeting, seated

    during_meeting, seated = bridge.run_beside(scenario)
    assert during_meeting["attached"] is False
    assert seated["attached"] is True
    assert bridge.heard.read_bytes() == MICROPHONE
    assert bridge.meeting_heard.read_bytes() == CALL


def test_a_second_meeting_socket_is_refused_until_the_first_leaves(bridge):
    async def scenario():
        async with bridge.meeting_socket() as first:
            await first.send(CALL)
            await written(bridge.meeting_heard, len(CALL))
            async with bridge.meeting_socket() as second:
                with pytest.raises(ConnectionClosed) as refused:
                    await asyncio.wait_for(second.recv(), 5)
            code = refused.value.rcvd.code
        await asyncio.sleep(0.2)
        async with bridge.meeting_socket() as third:
            await third.send(CALL)
            await asyncio.sleep(0.1)
            return code, third.state.name

    code, state = bridge.run_beside(scenario)
    assert code == meeting_relay.MEETING_TAKEN_CODE
    assert state == "OPEN"


def test_a_meeting_page_from_another_origin_is_refused(bridge):
    async def scenario():
        with pytest.raises(InvalidStatus) as refused:
            async with bridge.meeting_socket(origin="https://example.com"):
                pass
        return refused.value.response.status_code

    assert bridge.run_beside(scenario) == 403


def test_a_meeting_whose_audio_tool_cannot_start_is_released(bridge, monkeypatch):
    original_path = os.environ["PATH"]
    monkeypatch.setenv("PATH", "/nonexistent")

    async def scenario():
        async with bridge.meeting_socket() as meeting:
            with pytest.raises(ConnectionClosed):
                await asyncio.wait_for(meeting.recv(), 5)
        monkeypatch.setenv("PATH", original_path)
        async with bridge.meeting_socket() as again:
            await again.send(CALL)
            return await written(bridge.meeting_heard, len(CALL))

    assert bridge.run_beside(scenario) == CALL


def test_the_meeting_page_is_served_with_the_seat_page(bridge):
    (bridge.page / "meeting-seat.js").write_text("export const meeting = 1;")

    async def scenario():
        return await bridge.fetch("/meeting-seat.js")

    assert bridge.run_beside(scenario) == (200, b"export const meeting = 1;")


def test_the_page_files_name_the_meeting_module_beside_the_seat_script(tmp_path):
    files = seat_page.seat_page_files(tmp_path)
    assert files["/meeting-seat.js"] == (
        tmp_path / "meeting-seat.js",
        seat_page.JAVASCRIPT,
    )
    assert "/seat.js" in files


def test_a_meeting_alone_does_not_keep_the_bridge_running(bridge, monkeypatch):
    monkeypatch.setattr(seat_bridge, "FIRST_ATTACH_SECONDS", 0.3)

    async def scenario():
        serving = asyncio.create_task(bridge.serve())
        await bridge.listening()
        async with bridge.meeting_socket() as meeting:
            await meeting.send(CALL)
            await asyncio.wait_for(serving, 5)

    asyncio.run(scenario())
