from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class VoicePipelineConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VOICE_PIPELINE_")

    gateway_url: str = "http://localhost:18789"
    gateway_token_file: str = "/run/agenix/openclaw-gateway-token"
    default_agent: str = "jarvis"

    stt_engine: Literal["deepgram", "openai-whisper"] = "deepgram"
    stt_mode: Literal["vad-gated", "always-streaming"] = "vad-gated"
    deepgram_api_key_file: str = ""

    tts_voice: str = "onyx"
    openai_api_key_file: str = ""

    vad_threshold: float = 0.5
    vad_min_silence_ms: int = 300
    vad_model_path: str = ""

    wake_words: list[str] = ["jarvis"]

    conversation_window_seconds: float = 15.0
    max_history_turns: int = 20

    capture_device: str = "echo-cancel-source"
    sample_rate: int = 16000
    frame_duration_ms: int = 30

    barge_in_enabled: bool = True

    socket_path: str = "/tmp/voice-pipeline.sock"

    agent_voices: dict[str, str] = {}

    model: str = "anthropic/claude-sonnet-4-5"

    def read_secret(self, path: str) -> str:
        if not path:
            return ""
        try:
            with open(path) as f:
                return f.read().strip()
        except FileNotFoundError:
            return ""
