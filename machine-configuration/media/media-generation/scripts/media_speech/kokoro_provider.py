from pathlib import Path

from media_speech.contract import SpeechError, SpeechRequest, SynthesizedSpeech
from media_speech.discovery import (
    SpeechCapabilities,
    SpeechVoice,
    SpeechVoicePage,
    VoiceQuery,
)

KOKORO_VOICES = (
    SpeechVoice("af_heart", "Heart", "en-us"),
    SpeechVoice("af_bella", "Bella", "en-us"),
    SpeechVoice("am_adam", "Adam", "en-us"),
    SpeechVoice("pf_dora", "Dora", "pt-br"),
    SpeechVoice("pm_alex", "Alex", "pt-br"),
    SpeechVoice("pm_santa", "Santa", "pt-br"),
)


class KokoroVoiceCatalog:
    def list_voices(self, query: VoiceQuery):
        voices = tuple(
            voice
            for voice in KOKORO_VOICES
            if query.search is None
            or query.search.casefold() in voice.name.casefold()
            or query.search.casefold() in voice.voice_id.casefold()
        )
        start = 0
        if query.page_token is not None:
            if not query.page_token.isascii() or not query.page_token.isdecimal():
                raise SpeechError("invalid_page_token")
            start = int(query.page_token)
            if start >= len(voices):
                raise SpeechError("invalid_page_token")
        end = start + query.page_size
        return SpeechVoicePage(
            voices[start:end], str(end) if end < len(voices) else None
        )


class KokoroSpeechProvider:
    name = "kokoro"
    model = "kokoro-v1.0-int8-model-files-v1.0"
    requires_payment = False

    @classmethod
    def describe(cls):
        return SpeechCapabilities(
            cls.name,
            cls.model,
            "local",
            cls.requires_payment,
            False,
            "unavailable",
            True,
            "bundled",
        )

    def __init__(
        self, model: Path, voices: Path, espeak_library: Path, espeak_data: Path
    ):
        self.model_path = model
        self.voices_path = voices
        self.espeak_library = espeak_library
        self.espeak_data = espeak_data

    def preflight(self, request: SpeechRequest):
        if not any(
            voice.voice_id == request.voice and voice.language == request.language
            for voice in KOKORO_VOICES
        ):
            raise SpeechError("unsupported_voice")
        if (
            not all(
                path.is_file()
                for path in (self.model_path, self.voices_path, self.espeak_library)
            )
            or not self.espeak_data.is_dir()
        ):
            raise SpeechError("local_runtime_unavailable")

    def synthesize(self, request: SpeechRequest):
        import numpy
        import onnxruntime
        from kokoro_onnx import Kokoro
        from kokoro_onnx.config import EspeakConfig

        session_options = onnxruntime.SessionOptions()
        session_options.intra_op_num_threads = 2
        session_options.inter_op_num_threads = 1
        session = onnxruntime.InferenceSession(
            str(self.model_path),
            sess_options=session_options,
            providers=["CPUExecutionProvider"],
        )
        runtime = Kokoro.from_session(
            session,
            str(self.voices_path),
            espeak_config=EspeakConfig(
                lib_path=str(self.espeak_library), data_path=str(self.espeak_data)
            ),
        )
        audio, sample_rate = runtime.create(
            request.text, voice=request.voice, lang=request.language
        )
        if audio.ndim != 1 or not numpy.isfinite(audio).all():
            raise SpeechError("invalid_audio")
        pcm_audio = (numpy.clip(audio, -1, 1) * 32767).astype("<i2").tobytes()
        return SynthesizedSpeech(pcm_audio=pcm_audio, sample_rate_hz=sample_rate)
