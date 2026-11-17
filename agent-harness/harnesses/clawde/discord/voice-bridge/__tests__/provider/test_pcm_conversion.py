import struct

from hypothesis import given, strategies as st

from voice_provider.pcm_conversion import (
    capture_pcm_from_discord_pcm,
    mono_pcm_from_interleaved,
)

SAMPLE = st.integers(min_value=-32768, max_value=32767)
FRAME = st.tuples(SAMPLE, SAMPLE)


def stereo_pcm(frames):
    return b"".join(struct.pack("<hh", left, right) for left, right in frames)


def samples_of(pcm):
    return struct.unpack(f"<{len(pcm) // 2}h", pcm)


@given(st.lists(FRAME, max_size=300))
def test_length_is_one_third_of_the_frames(frames):
    converted = capture_pcm_from_discord_pcm(stereo_pcm(frames))

    assert len(converted) // 2 == len(frames) // 3


@given(SAMPLE, st.integers(min_value=0, max_value=100))
def test_a_constant_signal_stays_constant(level, group_count):
    converted = capture_pcm_from_discord_pcm(
        stereo_pcm([(level, level)] * (group_count * 3))
    )

    assert set(samples_of(converted)) <= {level}
    assert len(converted) == group_count * 2


@given(st.integers(min_value=0, max_value=100))
def test_silence_stays_zero(group_count):
    converted = capture_pcm_from_discord_pcm(bytes(group_count * 3 * 4))

    assert converted == bytes(group_count * 2)


@given(st.lists(FRAME, min_size=3, max_size=300))
def test_each_output_sample_stays_within_the_input_range(frames):
    converted = samples_of(capture_pcm_from_discord_pcm(stereo_pcm(frames)))
    channel_values = [value for frame in frames for value in frame]

    assert all(
        min(channel_values) <= value <= max(channel_values) for value in converted
    )


@given(st.lists(FRAME, max_size=200))
def test_stereo_playback_clip_averages_the_channels(frames):
    mono = samples_of(mono_pcm_from_interleaved(stereo_pcm(frames), 2))

    assert list(mono) == [(left + right) >> 1 for left, right in frames]


@given(st.lists(SAMPLE, max_size=200))
def test_mono_playback_clip_is_unchanged(samples):
    pcm = struct.pack(f"<{len(samples)}h", *samples)

    assert mono_pcm_from_interleaved(pcm, 1) == pcm
