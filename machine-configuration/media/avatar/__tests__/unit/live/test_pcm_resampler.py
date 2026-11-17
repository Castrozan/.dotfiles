import array
import itertools

from hypothesis import given
from hypothesis import strategies as st
from pcm_resampler import LinearResampler

RATES = st.sampled_from([8000, 16000, 22050, 24000, 44100, 48000])
SAMPLES = st.lists(st.integers(-32768, 32767), min_size=1, max_size=400)


def pcm_of(samples):
    return array.array("h", samples).tobytes()


def samples_of(pcm):
    decoded = array.array("h")
    decoded.frombytes(pcm)
    return list(decoded)


def ceiling_division(numerator, denominator):
    return -(-numerator // denominator)


@given(RATES, RATES, SAMPLES)
def test_the_length_follows_the_rate_ratio_holding_back_only_the_last_sample(
    source_rate, target_rate, samples
):
    resampled = samples_of(
        LinearResampler(source_rate, target_rate).resample(pcm_of(samples))
    )
    assert len(resampled) == ceiling_division(
        (len(samples) - 1) * target_rate, source_rate
    )
    expected = (len(samples) - 1) * target_rate / source_rate
    assert expected <= len(resampled) < expected + 1


@given(RATES, RATES, st.integers(-32768, 32767), st.integers(1, 400))
def test_a_constant_signal_stays_exactly_constant(
    source_rate, target_rate, level, length
):
    resampled = samples_of(
        LinearResampler(source_rate, target_rate).resample(pcm_of([level] * length))
    )
    assert set(resampled) <= {level}


@given(RATES, RATES, SAMPLES)
def test_the_output_never_leaves_the_range_of_the_input(
    source_rate, target_rate, samples
):
    resampled = samples_of(
        LinearResampler(source_rate, target_rate).resample(pcm_of(samples))
    )
    assert all(min(samples) <= sample <= max(samples) for sample in resampled)


@given(RATES, RATES, SAMPLES, st.lists(st.integers(1, 400), max_size=6))
def test_cutting_the_stream_into_chunks_changes_nothing(
    source_rate, target_rate, samples, cuts
):
    whole = LinearResampler(source_rate, target_rate).resample(pcm_of(samples))
    streaming = LinearResampler(source_rate, target_rate)
    boundaries = sorted({0, len(samples), *(cut % (len(samples) + 1) for cut in cuts)})
    pieces = [
        streaming.resample(pcm_of(samples[start:end]))
        for start, end in itertools.pairwise(boundaries)
    ]
    assert b"".join(pieces) == whole


def test_the_same_rate_passes_the_samples_through_one_behind():
    samples = [3, -7, 11, 5]
    resampled = LinearResampler(16000, 16000).resample(pcm_of(samples))
    assert samples_of(resampled) == samples[:-1]


def test_a_ramp_upsampled_by_one_and_a_half_interpolates_linearly():
    resampled = LinearResampler(16000, 24000).resample(pcm_of([0, 3, 6, 9]))
    assert samples_of(resampled) == [0, 2, 4, 6, 8]


def test_an_empty_chunk_yields_nothing_and_keeps_the_position():
    resampler = LinearResampler(16000, 24000)
    assert resampler.resample(b"") == b""
    assert samples_of(resampler.resample(pcm_of([0, 3, 6, 9]))) == [0, 2, 4, 6, 8]
