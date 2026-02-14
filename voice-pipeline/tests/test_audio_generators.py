import io
import wave

import numpy as np

from tests.conftest import (
    SAMPLE_RATE,
    FRAME_SIZE,
    generate_silence,
    generate_sine_wave,
    generate_white_noise,
    generate_speech_like_signal,
    pcm_to_wav_bytes,
    split_into_frames,
)


class TestSilenceGenerator:
    def test_correct_length(self):
        pcm = generate_silence(duration_ms=100)
        expected_samples = int(SAMPLE_RATE * 100 / 1000)
        assert len(pcm) == expected_samples * 2

    def test_all_zeros(self):
        pcm = generate_silence()
        arr = np.frombuffer(pcm, dtype=np.int16)
        assert np.all(arr == 0)

    def test_default_30ms(self):
        pcm = generate_silence()
        expected_samples = int(SAMPLE_RATE * 30 / 1000)
        assert len(pcm) == expected_samples * 2


class TestSineWaveGenerator:
    def test_correct_length(self):
        pcm = generate_sine_wave(duration_ms=100)
        expected_samples = int(SAMPLE_RATE * 100 / 1000)
        assert len(pcm) == expected_samples * 2

    def test_not_silence(self):
        pcm = generate_sine_wave()
        arr = np.frombuffer(pcm, dtype=np.int16)
        assert np.max(np.abs(arr)) > 0

    def test_amplitude_scaling(self):
        loud = generate_sine_wave(amplitude=1.0)
        quiet = generate_sine_wave(amplitude=0.1)
        loud_arr = np.frombuffer(loud, dtype=np.int16)
        quiet_arr = np.frombuffer(quiet, dtype=np.int16)
        assert np.max(np.abs(loud_arr)) > np.max(np.abs(quiet_arr))

    def test_int16_range(self):
        pcm = generate_sine_wave(amplitude=1.0)
        arr = np.frombuffer(pcm, dtype=np.int16)
        assert arr.max() <= 32767
        assert arr.min() >= -32768


class TestWhiteNoiseGenerator:
    def test_correct_length(self):
        pcm = generate_white_noise(duration_ms=50)
        expected_samples = int(SAMPLE_RATE * 50 / 1000)
        assert len(pcm) == expected_samples * 2

    def test_not_silence(self):
        pcm = generate_white_noise()
        arr = np.frombuffer(pcm, dtype=np.int16)
        assert np.std(arr) > 0

    def test_random_distribution(self):
        pcm = generate_white_noise(duration_ms=1000)
        arr = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32767
        assert abs(np.mean(arr)) < 0.1


class TestSpeechLikeSignal:
    def test_correct_length(self):
        pcm = generate_speech_like_signal(duration_ms=500)
        expected_samples = int(SAMPLE_RATE * 500 / 1000)
        assert len(pcm) == expected_samples * 2

    def test_has_fundamental_frequency(self):
        pcm = generate_speech_like_signal(duration_ms=1000)
        arr = np.frombuffer(pcm, dtype=np.int16).astype(np.float32)
        fft = np.abs(np.fft.rfft(arr))
        freqs = np.fft.rfftfreq(len(arr), d=1.0 / SAMPLE_RATE)
        fundamental_idx = np.argmin(np.abs(freqs - 150))
        peak_region = fft[fundamental_idx - 2 : fundamental_idx + 3]
        assert np.max(peak_region) > np.mean(fft) * 2

    def test_envelope_fades(self):
        pcm = generate_speech_like_signal(duration_ms=500)
        arr = np.frombuffer(pcm, dtype=np.int16).astype(np.float32)
        first_samples = np.abs(arr[:10])
        middle_samples = np.abs(arr[len(arr) // 2 - 5 : len(arr) // 2 + 5])
        assert np.mean(first_samples) < np.mean(middle_samples)


class TestPcmToWav:
    def test_valid_wav(self):
        pcm = generate_sine_wave(duration_ms=100)
        wav_data = pcm_to_wav_bytes(pcm)
        buffer = io.BytesIO(wav_data)
        with wave.open(buffer, "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
            assert wf.getframerate() == SAMPLE_RATE
            assert wf.readframes(wf.getnframes()) == pcm

    def test_wav_header_present(self):
        pcm = generate_silence(duration_ms=10)
        wav_data = pcm_to_wav_bytes(pcm)
        assert wav_data[:4] == b"RIFF"


class TestSplitIntoFrames:
    def test_correct_frame_count(self):
        pcm = generate_sine_wave(duration_ms=300)
        frames = split_into_frames(pcm)
        expected_frames = 300 // 30
        assert len(frames) == expected_frames

    def test_frame_size_bytes(self):
        pcm = generate_sine_wave(duration_ms=60)
        frames = split_into_frames(pcm)
        for frame in frames:
            assert len(frame) == FRAME_SIZE * 2

    def test_incomplete_frames_dropped(self):
        pcm = generate_sine_wave(duration_ms=45)
        frames = split_into_frames(pcm)
        assert len(frames) == 1
