import asyncio
import socket

import mac_microphone
import pytest
from websockets.exceptions import ConnectionClosed, InvalidStatus

FRAMES = [b"\x01\x02" * 320, b"\x03\x04" * 320, b"\x05\x06" * 320]


def test_every_binary_frame_the_page_sends_reaches_the_output_in_order(microphone):
    async def scenario():
        async with microphone.page() as relay_socket:
            for frame in FRAMES:
                await relay_socket.send(frame)
            await relay_socket.send("text is not audio")
        await asyncio.sleep(0.2)

    assert microphone.run_beside(scenario) == b"".join(FRAMES)
    assert microphone.output.flushes == len(FRAMES)


def test_the_relay_ends_when_the_page_leaves(microphone):
    async def run():
        relaying = asyncio.create_task(microphone.relay())
        await microphone.listening()
        async with microphone.page() as relay_socket:
            await relay_socket.send(FRAMES[0])
        await asyncio.wait_for(relaying, 5)

    asyncio.run(run())
    assert microphone.output.getvalue() == FRAMES[0]


def test_a_second_page_is_turned_away_while_the_first_holds_the_microphone(
    microphone,
):
    async def scenario():
        async with microphone.page() as first:
            await first.send(FRAMES[0])
            async with microphone.page() as second:
                with pytest.raises(ConnectionClosed) as turned_away:
                    await second.recv()
            await first.send(FRAMES[1])
        assert turned_away.value.rcvd.code == mac_microphone.PAGE_TAKEN_CODE
        await asyncio.sleep(0.2)

    assert microphone.run_beside(scenario) == FRAMES[0] + FRAMES[1]


@pytest.mark.parametrize("origin", ["http://evil.example", "http://localhost:1"])
def test_a_page_from_another_origin_cannot_open_the_socket(microphone, origin):
    async def scenario():
        with pytest.raises(InvalidStatus) as refused:
            async with microphone.page(origin):
                pass
        assert refused.value.response.status_code == 403

    assert microphone.run_beside(scenario) == b""


def test_the_capture_page_and_the_shared_worklets_are_served(microphone):
    async def scenario():
        assert await microphone.fetch("/") == (200, b"<p>wake</p>")
        assert await microphone.fetch("/microphone-choice.js") == (200, b"choice")
        assert await microphone.fetch("/seat-audio-worklets.js") == (200, b"worklets")
        assert await microphone.fetch("/seat.js") == (404, b"")

    microphone.run_beside(scenario)


def test_the_browser_page_is_opened_only_once_the_relay_listens(
    microphone, monkeypatch
):
    monkeypatch.setattr(mac_microphone, "ATTACH_SECONDS", 0.1)

    def open_page_by_connecting():
        with socket.create_connection(("127.0.0.1", microphone.port), timeout=2):
            pass

    microphone.open_page.side_effect = open_page_by_connecting
    with pytest.raises(TimeoutError):
        asyncio.run(microphone.relay())
    microphone.open_page.assert_called_once_with()


def test_no_page_within_the_wait_ends_the_relay_with_a_timeout(microphone, monkeypatch):
    monkeypatch.setattr(mac_microphone, "ATTACH_SECONDS", 0.1)
    with pytest.raises(TimeoutError):
        asyncio.run(microphone.relay())
