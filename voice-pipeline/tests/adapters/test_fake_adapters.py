import pytest

from tests.conftest import (
    FakeAudioCapture,
    FakeAudioPlayback,
    FakeVad,
    FakeTranscriber,
    FakeCompletion,
    FakeSynthesizer,
    generate_silence,
    generate_sine_wave,
)
from voice_pipeline.ports.transcriber import TranscriptEvent


class TestFakeAudioCapture:
    @pytest.mark.asyncio
    async def test_start_stop(self, fake_capture):
        await fake_capture.start()
        assert fake_capture._started
        await fake_capture.stop()
        assert not fake_capture._started

    @pytest.mark.asyncio
    async def test_read_frames(self):
        frames = [generate_silence() for _ in range(3)]
        capture = FakeAudioCapture(frames=frames)
        collected = []
        async for frame in capture.read_frames():
            collected.append(frame)
        assert len(collected) == 3

    @pytest.mark.asyncio
    async def test_feed_frames(self, fake_capture):
        fake_capture.feed_frames([generate_silence()])
        collected = []
        async for frame in fake_capture.read_frames():
            collected.append(frame)
        assert len(collected) == 1

    def test_sample_rate(self, fake_capture):
        assert fake_capture.sample_rate == 16000

    def test_frame_size(self, fake_capture):
        assert fake_capture.frame_size == 480


class TestFakeAudioPlayback:
    @pytest.mark.asyncio
    async def test_play_chunk(self, fake_playback):
        await fake_playback.start()
        await fake_playback.play_chunk(b"\x00" * 100)
        assert len(fake_playback.played_chunks) == 1
        assert fake_playback.total_bytes_played == 100

    @pytest.mark.asyncio
    async def test_cancel_clears_queue(self, fake_playback):
        await fake_playback.start()
        await fake_playback.play_chunk(b"\x00" * 100)
        await fake_playback.cancel()
        assert len(fake_playback.played_chunks) == 0

    @pytest.mark.asyncio
    async def test_play_after_cancel_ignored(self, fake_playback):
        await fake_playback.start()
        await fake_playback.cancel()
        await fake_playback.play_chunk(b"\x00" * 100)
        assert fake_playback.total_bytes_played == 0


class TestFakeVad:
    def test_returns_probabilities_in_order(self):
        vad = FakeVad(probabilities=[0.1, 0.8, 0.3])
        assert vad.process_frame(b"") == 0.1
        assert vad.process_frame(b"") == 0.8
        assert vad.process_frame(b"") == 0.3

    def test_returns_zero_after_exhausted(self):
        vad = FakeVad(probabilities=[0.9])
        assert vad.process_frame(b"") == 0.9
        assert vad.process_frame(b"") == 0.0

    def test_reset(self):
        vad = FakeVad(probabilities=[0.5, 0.6])
        vad.process_frame(b"")
        vad.reset()
        assert vad.process_frame(b"") == 0.5

    def test_set_probabilities(self):
        vad = FakeVad()
        vad.set_probabilities([0.7, 0.8])
        assert vad.process_frame(b"") == 0.7


class TestFakeTranscriber:
    @pytest.mark.asyncio
    async def test_session_lifecycle(self, fake_transcriber):
        await fake_transcriber.start_session()
        assert fake_transcriber._session_active
        await fake_transcriber.close_session()
        assert not fake_transcriber._session_active

    @pytest.mark.asyncio
    async def test_send_audio(self, fake_transcriber):
        await fake_transcriber.start_session()
        await fake_transcriber.send_audio(b"\x00" * 100)
        assert len(fake_transcriber._audio_received) == 1

    @pytest.mark.asyncio
    async def test_get_transcripts(self, fake_transcriber):
        fake_transcriber.queue_events([
            TranscriptEvent(text="hello jarvis", is_final=False),
            TranscriptEvent(text="hello jarvis what time is it", is_final=True),
        ])
        results = []
        async for event in fake_transcriber.get_transcripts():
            results.append(event)
        assert len(results) == 2
        assert results[1].is_final


class TestFakeCompletion:
    @pytest.mark.asyncio
    async def test_stream_default(self, fake_completion):
        chunks = []
        async for chunk in fake_completion.stream([], "jarvis"):
            chunks.append(chunk)
        assert "".join(chunks) == "Hello there!"

    @pytest.mark.asyncio
    async def test_stream_custom_agent(self):
        completion = FakeCompletion(responses={
            "robson": ["Oi", " tudo bem?"],
        })
        chunks = []
        async for chunk in completion.stream([], "robson"):
            chunks.append(chunk)
        assert "".join(chunks) == "Oi tudo bem?"

    @pytest.mark.asyncio
    async def test_cancel(self, fake_completion):
        await fake_completion.cancel()
        assert fake_completion._cancelled


class TestFakeSynthesizer:
    @pytest.mark.asyncio
    async def test_synthesize(self, fake_synthesizer):
        chunks = []
        async for chunk in fake_synthesizer.synthesize("hello", "onyx"):
            chunks.append(chunk)
        assert len(chunks) == 3
        assert fake_synthesizer._synthesize_count == 1

    @pytest.mark.asyncio
    async def test_cancel(self, fake_synthesizer):
        await fake_synthesizer.cancel()
        assert fake_synthesizer._cancelled
