import asyncio
import sys
import time

import mac_room_audio
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from mac_room_fakes import RATE, eventually, room

SECONDS_PER_CHUNK = mac_room_audio.CHUNK_SECONDS


def whole_chunks(sizes):
    return [bytes([index % 251]) * (size * 2) for index, size in enumerate(sizes)]


@settings(max_examples=25, deadline=None)
@given(st.lists(st.integers(1, 3000), min_size=1, max_size=4))
def test_every_sample_reaches_the_seat_once_in_order_in_short_chunks(sizes):
    pieces = whole_chunks(sizes)
    with room() as fakes:
        speaker = fakes.speaker()
        for piece in pieces:
            speaker.play(piece)
        eventually(lambda: len(b"".join(fakes.stream.sent)) == len(b"".join(pieces)))
        assert b"".join(fakes.stream.sent) == b"".join(pieces)
        assert all(len(chunk) <= speaker.chunk_bytes for chunk in fakes.stream.sent)


def test_speech_reaches_the_seat_no_faster_than_it_is_spoken_plus_the_lead():
    seconds = 0.6
    with room(lead_seconds=mac_room_audio.LEAD_SECONDS) as fakes:
        fakes.speaker().play(bytes(int(RATE * seconds) * 2))
        eventually(lambda: sum(map(len, fakes.stream.sent)) == int(RATE * seconds) * 2)
    sent_over = fakes.stream.sent_at[-1] - fakes.stream.sent_at[0]
    assert sent_over >= seconds - mac_room_audio.LEAD_SECONDS - 2 * SECONDS_PER_CHUNK


def test_what_is_waiting_to_play_counts_as_buffered():
    with room() as fakes:
        fakes.stream.opening.clear()
        speaker = fakes.speaker()
        speaker.play(bytes(speaker.chunk_bytes * 5))
        eventually(lambda: speaker.pending.qsize() == 4)
        assert speaker.buffered_seconds() == pytest.approx(4 * SECONDS_PER_CHUNK)
        fakes.stream.opening.set()


def test_clearing_hushes_the_seat_closes_the_mouth_and_drops_what_was_waiting():
    with room() as fakes:
        fakes.stream.opening.clear()
        speaker = fakes.speaker()
        speaker.play(bytes(speaker.chunk_bytes * 5))
        eventually(lambda: speaker.pending.qsize() == 4)
        speaker.clear()
        assert fakes.stream.cleared == 1
        assert fakes.connection.levels()[-1] == 0.0
        assert speaker.buffered_seconds() == 0
        fakes.stream.opening.set()
        time.sleep(0.2)
        assert fakes.stream.sent == []
        speaker.play(bytes(speaker.chunk_bytes))
        eventually(lambda: len(fakes.stream.sent) == 1)


def test_the_mouth_follows_the_loudness_of_each_chunk_then_closes():
    loud = (8192).to_bytes(2, "little", signed=True) * 960
    with room() as fakes:
        fakes.speaker().play(loud * 3)
        eventually(lambda: fakes.connection.levels()[-1:] == [0.0])
    levels = fakes.connection.levels()
    assert [level for level in levels if level] == [pytest.approx(0.25)] * 3


def test_closing_closes_the_mouth_the_stream_and_the_control_connection():
    with room() as fakes:
        fakes.speaker().close()
        assert fakes.connection.levels()[-1] == 0.0
        assert fakes.connection.closed
        assert fakes.stream.closed


def test_a_broken_seat_stops_the_voice_loudly_instead_of_muting_it():
    with room() as fakes:
        fakes.stream.failure = BrokenPipeError(32, "Broken pipe")
        speaker = fakes.speaker()
        speaker.play(bytes(speaker.chunk_bytes))
        eventually(lambda: speaker.failure is not None)
        with pytest.raises(BrokenPipeError):
            speaker.play(bytes(speaker.chunk_bytes))


def test_a_lost_control_server_stops_the_voice_instead_of_freezing_the_mouth():
    with room() as fakes:
        speaker = fakes.speaker()
        fakes.connection.failure = BrokenPipeError(32, "Broken pipe")
        speaker.play(bytes(speaker.chunk_bytes))
        eventually(lambda: speaker.mouth.failure is not None)
        with pytest.raises(BrokenPipeError):
            speaker.play(bytes(speaker.chunk_bytes))


def test_the_seat_microphone_arrives_at_the_model_rate(monkeypatch):
    seat_output = "import sys; sys.stdout.buffer.write(bytes(6400))"
    monkeypatch.setattr(
        mac_room_audio.mac_seat_client,
        "capture_command",
        lambda device: [sys.executable, "-c", seat_output],
    )

    async def heard():
        chunks = []
        with pytest.raises(asyncio.IncompleteReadError):
            async for chunk in mac_room_audio.microphone_chunks(RATE, "ignored"):
                chunks.append(chunk)
        return chunks

    assert [len(chunk) for chunk in asyncio.run(heard())] == [4798, 4800]
