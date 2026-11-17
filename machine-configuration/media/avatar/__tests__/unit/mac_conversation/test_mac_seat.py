import asyncio
import time
from types import SimpleNamespace
from unittest.mock import patch

import mac_seat
import mac_seat_client
from hypothesis import given
from hypothesis import strategies as st


class Page:
    def __init__(self):
        self.chunks = []
        self.sent_at = []

    async def send(self, chunk):
        self.chunks.append(chunk)
        self.sent_at.append(time.monotonic())


async def no_wait(seconds):
    return None


def seat_with_a_page():
    seat = mac_seat.MacSeat({}, SimpleNamespace())
    seat.page_socket = Page()
    return seat


def played(seat, pcm, hushed=None):
    async def scenario():
        await seat.play(pcm, hushed or asyncio.Event())

    asyncio.run(scenario())
    return seat.page_socket.chunks


@given(st.binary(max_size=mac_seat.CHUNK_BYTES * 4 + 3))
def test_every_whole_sample_reaches_the_page_once_and_in_order(pcm):
    with patch.object(mac_seat.asyncio, "sleep", no_wait):
        chunks = played(seat_with_a_page(), pcm)
    assert b"".join(chunks) == pcm[: len(pcm) - len(pcm) % 2]
    assert all(len(chunk) % 2 == 0 for chunk in chunks)
    assert all(len(chunk) <= mac_seat.CHUNK_BYTES for chunk in chunks)


def test_speech_reaches_the_page_no_faster_than_it_is_spoken():
    seconds = 0.4
    seat = seat_with_a_page()
    played(seat, bytes(int(mac_seat.VOICE_RATE * seconds) * 2))
    sent_over = seat.page_socket.sent_at[-1] - seat.page_socket.sent_at[0]
    assert sent_over >= seconds - mac_seat.LEAD_SECONDS - 2 * mac_seat.CHUNK_SECONDS


def test_hushed_speech_sends_nothing_more():
    async def scenario():
        hushed = asyncio.Event()
        hushed.set()
        await seat.play(bytes(mac_seat.CHUNK_BYTES * 3), hushed)

    seat = seat_with_a_page()
    asyncio.run(scenario())
    assert seat.page_socket.chunks == []


def test_speech_without_a_page_ends_at_once():
    async def scenario():
        await seat.play(bytes(mac_seat.CHUNK_BYTES * 3), asyncio.Event())

    seat = mac_seat.MacSeat({}, SimpleNamespace())
    asyncio.run(scenario())


def test_a_new_speech_silences_the_one_before_it():
    class Speaker:
        async def recv(self):
            return "not audio"

    async def scenario():
        seat = seat_with_a_page()
        earlier = seat.hushed
        await seat.carry_speech(Speaker())
        return earlier.is_set(), seat.hushed.is_set()

    assert asyncio.run(scenario()) == (True, False)


def test_asking_for_silence_hushes_the_speech_in_progress():
    async def scenario():
        seat = seat_with_a_page()
        request = SimpleNamespace(path=mac_seat_client.HUSH_PATH)
        answer = seat.answer_request(SimpleNamespace(), request)
        return seat.hushed.is_set(), answer.status_code

    assert asyncio.run(scenario()) == (True, 200)


def test_the_speech_path_is_left_to_the_websocket():
    async def scenario():
        request = SimpleNamespace(path=mac_seat_client.SPEECH_PATH)
        return seat_with_a_page().answer_request(SimpleNamespace(), request)

    assert asyncio.run(scenario()) is None
