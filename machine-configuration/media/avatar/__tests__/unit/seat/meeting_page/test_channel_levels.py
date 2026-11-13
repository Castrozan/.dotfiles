import asyncio
import subprocess
import time

import channel_levels
import pytest
from hypothesis import given
from hypothesis import strategies as st

SINK_NAMES = {"agent": "AvatarMic", "human": "AvatarHuman"}


def sink(name, percents, mute=False):
    return {
        "name": name,
        "mute": mute,
        "volume": {
            f"channel-{position}": {"value_percent": f"{percent}%"}
            for position, percent in enumerate(percents)
        },
    }


percent_lists = st.lists(st.integers(0, 400), min_size=1, max_size=8)


@given(percents=percent_lists)
def test_an_audible_sink_gains_the_mean_of_its_channels_within_zero_and_one(percents):
    levels = channel_levels.levels_from_sinks([sink("AvatarMic", percents)])
    expected = min(sum(percents) / len(percents) / 100, 1.0)
    assert 0.0 <= levels["agent"] <= 1.0
    assert levels["agent"] == pytest.approx(expected)


@given(percents=percent_lists)
def test_a_muted_sink_gains_nothing_whatever_its_volume(percents):
    levels = channel_levels.levels_from_sinks(
        [sink("AvatarHuman", percents, mute=True)]
    )
    assert levels == {"human": 0.0}


@given(
    present=st.sets(st.sampled_from(sorted(SINK_NAMES))), percent=st.integers(0, 100)
)
def test_only_the_channels_whose_sink_exists_are_reported(present, percent):
    sinks = [sink(SINK_NAMES[channel], [percent]) for channel in sorted(present)]
    sinks.append(sink("unrelated", [percent]))
    assert set(channel_levels.levels_from_sinks(sinks)) == present


def test_uneven_channels_average_and_an_overdriven_sink_clamps_to_full():
    levels = channel_levels.levels_from_sinks(
        [sink("AvatarMic", [100, 50]), sink("AvatarHuman", [150, 150])]
    )
    assert levels == {"agent": 0.75, "human": 1.0}


def test_the_current_levels_come_from_the_pulse_sinks(monkeypatch):
    monkeypatch.setattr(
        channel_levels.pulse_audio, "items", lambda kind: [sink("AvatarMic", [65])]
    )
    assert asyncio.run(channel_levels.current()) == {"agent": 0.65}


@pytest.mark.parametrize(
    "failure",
    [
        FileNotFoundError("pactl"),
        subprocess.CalledProcessError(1, "pactl"),
        subprocess.TimeoutExpired("pactl", 1),
    ],
)
def test_an_unreadable_pulse_leaves_the_levels_empty(monkeypatch, failure):
    def unreadable(kind):
        raise failure

    monkeypatch.setattr(channel_levels.pulse_audio, "items", unreadable)
    assert asyncio.run(channel_levels.current()) == {}


def test_a_pulse_that_never_answers_leaves_the_levels_empty(monkeypatch):
    monkeypatch.setattr(channel_levels, "READ_TIMEOUT_SECONDS", 0.05)
    monkeypatch.setattr(
        channel_levels.pulse_audio, "items", lambda kind: time.sleep(0.3)
    )
    assert asyncio.run(channel_levels.current()) == {}
