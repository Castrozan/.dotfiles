import array
import json
from unittest.mock import Mock

import mouth_levels
import pytest
from hypothesis import given
from hypothesis import strategies as st
from mouth_levels import MouthLevels, level_of


def pcm_of(samples):
    return array.array("h", samples).tobytes()


class Connection:
    def __init__(self):
        self.sent = []
        self.closed = False

    def send(self, message):
        self.sent.append(json.loads(message))

    def close(self):
        self.closed = True

    def levels(self):
        return [message["value"] for message in self.sent]


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


def mouth():
    connection, clock = Connection(), Clock()
    return MouthLevels(connection, clock), connection, clock


@given(st.lists(st.integers(-32768, 32767), max_size=200))
def test_a_level_is_always_between_silence_and_full_scale(samples):
    assert 0.0 <= level_of(pcm_of(samples)) <= 1.0


@given(st.integers(1, 32767), st.integers(1, 100))
def test_a_steady_tone_reads_as_its_amplitude(amplitude, length):
    expected = amplitude / mouth_levels.FULL_SCALE
    assert level_of(pcm_of([amplitude, -amplitude] * length)) == pytest.approx(expected)


def test_silence_and_nothing_both_read_as_zero():
    assert level_of(pcm_of([0] * 10)) == 0.0
    assert level_of(b"") == 0.0
    assert level_of(b"\x01") == 0.0


def test_a_level_reaches_the_mouth_only_when_the_page_plays_it():
    levels, connection, clock = mouth()
    levels.show(pcm_of([16384, -16384]))
    levels.deliver_due()
    assert connection.sent == []
    clock.now += mouth_levels.PAGE_PLAYBACK_DELAY_SECONDS
    levels.deliver_due()
    assert connection.sent == [{"type": "voiceLevel", "value": 0.5}]


def test_levels_arrive_in_the_order_the_chunks_were_shown():
    levels, connection, clock = mouth()
    for amplitude in (8192, 16384, 24576):
        levels.show(pcm_of([amplitude, -amplitude]))
        clock.now += 0.04
    clock.now += mouth_levels.PAGE_PLAYBACK_DELAY_SECONDS
    levels.deliver_due()
    assert connection.levels() == [0.25, 0.5, 0.75]


def test_the_mouth_closes_once_the_voice_has_stopped():
    levels, connection, clock = mouth()
    levels.show(pcm_of([16384, -16384]))
    clock.now += mouth_levels.PAGE_PLAYBACK_DELAY_SECONDS
    levels.deliver_due()
    clock.now += mouth_levels.IDLE_SECONDS
    levels.deliver_due()
    clock.now += 10
    levels.deliver_due()
    assert connection.levels() == [0.5, 0.0]


def test_it_waits_for_the_next_level_and_then_for_the_idle_moment():
    levels, _, clock = mouth()
    assert levels.seconds_until_next_delivery() is None
    levels.show(pcm_of([16384, -16384]))
    assert levels.seconds_until_next_delivery() == pytest.approx(
        mouth_levels.PAGE_PLAYBACK_DELAY_SECONDS
    )
    clock.now += mouth_levels.PAGE_PLAYBACK_DELAY_SECONDS
    levels.deliver_due()
    assert levels.seconds_until_next_delivery() == pytest.approx(
        mouth_levels.IDLE_SECONDS
    )


def test_silencing_drops_the_levels_not_yet_due_and_closes_the_mouth_now():
    levels, connection, clock = mouth()
    levels.show(pcm_of([16384, -16384]))
    levels.silence()
    clock.now += 10
    levels.deliver_due()
    assert connection.levels() == [0.0]


def test_closing_closes_the_mouth_and_the_connection():
    levels, connection, _ = mouth()
    levels.show(pcm_of([16384, -16384]))
    levels.close()
    assert connection.levels() == [0.0]
    assert connection.closed


def test_a_broken_connection_is_remembered_as_the_failure():
    class Broken(Connection):
        def send(self, message):
            raise BrokenPipeError(32, "Broken pipe")

    clock = Clock()
    levels = MouthLevels(Broken(), clock)
    levels.show(pcm_of([16384, -16384]))
    clock.now += 1
    levels.deliver_until_stopped()
    assert isinstance(levels.failure, BrokenPipeError)


def test_the_control_server_is_met_as_an_agent(monkeypatch):
    connection = Connection()
    connect = Mock(return_value=connection)
    monkeypatch.setattr(mouth_levels, "connect", connect)
    assert mouth_levels.open_control_connection() is connection
    assert connect.call_args.args == (mouth_levels.CONTROL_URL,)
    assert connection.sent == [{"type": "identify", "role": "agent"}]
