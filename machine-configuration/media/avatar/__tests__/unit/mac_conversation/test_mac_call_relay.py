import asyncio
import io
import socket
from types import SimpleNamespace

import mac_call_capture
import mac_microphone
import mac_seat
import mac_seat_client
import pytest
from websockets.asyncio.client import connect
from websockets.asyncio.server import serve

CALL_FRAMES = [b"\x01\x02" * 160, b"\x03\x04" * 160, b"\x05\x06" * 160]


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture
def seat_port(monkeypatch):
    port = free_port()
    monkeypatch.setattr(mac_seat_client, "PORT", port)
    monkeypatch.setattr(mac_seat_client, "ORIGIN", f"http://127.0.0.1:{port}")
    return port


def serving(seat, port):
    return serve(
        seat.carry,
        "127.0.0.1",
        port,
        origins=mac_microphone.allowed_origins(port),
        process_request=seat.answer_request,
    )


def connecting_to(port, path):
    return connect(f"ws://127.0.0.1:{port}{path}", origin=f"http://127.0.0.1:{port}")


async def until(condition):
    for _ in range(300):
        if condition():
            return
        await asyncio.sleep(0.01)
    raise TimeoutError("The condition never held")


def new_seat():
    return mac_seat.MacSeat({}, SimpleNamespace())


def run(scenario):
    return asyncio.run(asyncio.wait_for(scenario(), 10))


def test_the_call_frames_of_the_page_reach_a_capture_client_in_order(seat_port):
    async def scenario():
        seat = new_seat()
        async with serving(seat, seat_port):
            async with connecting_to(seat_port, mac_seat_client.CALL_PATH) as capturer:
                await until(lambda: seat.call.capturers)
                async with connecting_to(
                    seat_port, mac_seat_client.MEETING_PATH
                ) as page:
                    for frame in CALL_FRAMES:
                        await page.send(frame)
                    return [await capturer.recv() for _ in CALL_FRAMES]

    assert run(scenario) == CALL_FRAMES


def test_the_capture_program_writes_the_call_frames_it_receives(seat_port):
    async def scenario():
        seat = new_seat()
        output = io.BytesIO()
        async with serving(seat, seat_port):
            capture = asyncio.create_task(
                asyncio.to_thread(mac_call_capture.copy_call_audio, output)
            )
            await until(lambda: seat.call.capturers)
            async with connecting_to(seat_port, mac_seat_client.MEETING_PATH) as page:
                for frame in CALL_FRAMES:
                    await page.send(frame)
                await until(
                    lambda: len(output.getvalue()) == len(b"".join(CALL_FRAMES))
                )
        await capture
        return output.getvalue()

    assert run(scenario) == b"".join(CALL_FRAMES)


def test_every_connected_capture_client_hears_the_call(seat_port):
    async def scenario():
        seat = new_seat()
        async with serving(seat, seat_port):
            async with connecting_to(seat_port, mac_seat_client.CALL_PATH) as first:
                async with connecting_to(
                    seat_port, mac_seat_client.CALL_PATH
                ) as second:
                    await until(lambda: len(seat.call.capturers) == 2)
                    async with connecting_to(
                        seat_port, mac_seat_client.MEETING_PATH
                    ) as page:
                        await page.send(CALL_FRAMES[0])
                        return await first.recv(), await second.recv()

    assert run(scenario) == (CALL_FRAMES[0], CALL_FRAMES[0])


def test_a_second_page_is_refused_while_one_carries_the_call(seat_port):
    async def scenario():
        seat = new_seat()
        async with serving(seat, seat_port):
            async with connecting_to(seat_port, mac_seat_client.MEETING_PATH):
                await until(lambda: seat.call.carrying)
                async with connecting_to(
                    seat_port, mac_seat_client.MEETING_PATH
                ) as second:
                    await second.wait_closed()
                    return second.close_code

    assert run(scenario) == 1013


def test_a_capture_client_that_leaves_is_forgotten(seat_port):
    async def scenario():
        seat = new_seat()
        async with serving(seat, seat_port):
            async with connecting_to(seat_port, mac_seat_client.CALL_PATH):
                await until(lambda: seat.call.capturers)
            await until(lambda: not seat.call.capturers)

    run(scenario)


def test_the_meeting_and_call_paths_are_left_to_the_websocket():
    seat = new_seat()
    for path in (mac_seat_client.MEETING_PATH, mac_seat_client.CALL_PATH):
        assert (
            seat.answer_request(SimpleNamespace(), SimpleNamespace(path=path)) is None
        )
