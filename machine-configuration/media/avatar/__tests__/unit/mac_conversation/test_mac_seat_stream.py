import asyncio
import json
import socket
from types import SimpleNamespace

import mac_seat
import mac_seat_client
import pytest
from hypothesis import given
from hypothesis import strategies as st
from websockets.asyncio.server import serve


class Page:
    def __init__(self):
        self.messages = []

    async def send(self, message):
        self.messages.append(message)


class Listener:
    def __init__(self, *messages):
        self.messages = list(messages)
        self.closed_with = None

    async def recv(self):
        return self.messages.pop(0)

    async def close(self, code, reason):
        self.closed_with = code

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.messages:
            raise StopAsyncIteration
        return self.messages.pop(0)


def seat_with_a_page():
    seat = mac_seat.MacSeat({}, SimpleNamespace())
    seat.page_socket = Page()
    return seat


def header(rate=mac_seat.VOICE_RATE):
    return json.dumps({"sampleRate": rate})


def carried(seat, listener):
    asyncio.run(seat.carry_stream(listener))
    return seat.page_socket.messages


@given(st.lists(st.binary(max_size=64), max_size=8))
def test_every_whole_sample_streamed_reaches_the_page_in_order_unpaced(chunks):
    seat = seat_with_a_page()
    sent = carried(seat, Listener(header(), *chunks))
    assert b"".join(sent) == b"".join(
        chunk[: len(chunk) - len(chunk) % 2] for chunk in chunks
    )


def test_a_stream_at_another_rate_is_refused_before_any_audio_plays():
    listener = Listener(header(16000), b"\x01\x02")
    assert carried(seat_with_a_page(), listener) == []
    assert listener.closed_with == mac_seat.UNSUPPORTED_DATA_CODE


@pytest.mark.parametrize("opening", ["not json", "[]", "{}"])
def test_a_stream_without_a_rate_header_is_refused(opening):
    listener = Listener(opening, b"\x01\x02")
    assert carried(seat_with_a_page(), listener) == []
    assert listener.closed_with == mac_seat.UNSUPPORTED_DATA_CODE


def test_streamed_audio_without_a_page_is_dropped():
    seat = mac_seat.MacSeat({}, SimpleNamespace())
    asyncio.run(seat.carry_stream(Listener(header(), b"\x01\x02")))


def test_the_stream_path_is_left_to_the_websocket():
    request = SimpleNamespace(path=mac_seat_client.STREAM_PATH)
    assert seat_with_a_page().answer_request(SimpleNamespace(), request) is None


def test_the_websocket_paths_choose_their_carrier():
    async def scenario(path):
        carried_by = []

        async def carry_speech(websocket):
            carried_by.append("speech")

        async def carry_stream(websocket):
            carried_by.append("stream")

        seat = seat_with_a_page()
        seat.carry_speech, seat.carry_stream = carry_speech, carry_stream
        await seat.carry(SimpleNamespace(request=SimpleNamespace(path=path)))
        return carried_by

    assert asyncio.run(scenario(mac_seat_client.STREAM_PATH)) == ["stream"]
    assert asyncio.run(scenario(mac_seat_client.SPEECH_PATH)) == ["speech"]


def test_a_hush_clears_what_the_page_already_holds():
    async def scenario():
        seat = seat_with_a_page()
        request = SimpleNamespace(path=mac_seat_client.HUSH_PATH)
        seat.answer_request(SimpleNamespace(), request)
        await asyncio.sleep(0)
        return seat.page_socket.messages

    assert asyncio.run(scenario()) == [mac_seat.HUSH_MESSAGE]


def test_a_hush_without_a_page_only_stops_the_speech():
    async def scenario():
        seat = mac_seat.MacSeat({}, SimpleNamespace())
        seat.hush()
        return seat.hushed.is_set()

    assert asyncio.run(scenario()) is True


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def test_the_client_and_the_seat_agree_on_the_wire(monkeypatch):
    port = free_port()
    monkeypatch.setattr(mac_seat_client, "PORT", port)
    monkeypatch.setattr(mac_seat_client, "attached", lambda: True)
    voice = b"\x01\x02" * 480

    async def scenario():
        seat = seat_with_a_page()
        async with serve(seat.carry, "127.0.0.1", port):
            stream = mac_seat_client.SeatStream(mac_seat.VOICE_RATE)
            await asyncio.to_thread(stream.send, voice)
            await asyncio.to_thread(stream.send, voice)
            await asyncio.to_thread(stream.close)
            await asyncio.sleep(0.2)
        return seat.page_socket.messages

    assert asyncio.run(scenario()) == [voice, voice]
