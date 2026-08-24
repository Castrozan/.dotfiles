from __future__ import annotations

import os
from pathlib import Path

from assistant_gateway import GatewaySettings

WHISPER_MODEL_VARIABLE = "HEY_BOT_WHISPER_MODEL"
KEYWORDS_PATTERN_VARIABLE = "HEY_BOT_KEYWORDS_PATTERN"
GATEWAY_URL_VARIABLE = "HEY_BOT_GATEWAY_URL"
GATEWAY_TOKEN_FILE_VARIABLE = "HEY_BOT_GATEWAY_TOKEN_FILE"
AGENT_ID_VARIABLE = "HEY_BOT_AGENT_ID"
TTS_VOICE_VARIABLE = "HEY_BOT_TTS_VOICE"
MODEL_VARIABLE = "HEY_BOT_MODEL"
TRANSCRIPTION_DIRECTORY_VARIABLE = "HEY_BOT_TRANSCRIPTION_DIR"
MAX_LOG_SIZE_VARIABLE = "HEY_BOT_MAX_LOG_SIZE"


def whisper_model() -> str:
    return os.environ[WHISPER_MODEL_VARIABLE]


def keywords_pattern() -> str:
    return os.environ[KEYWORDS_PATTERN_VARIABLE]


def speech_voice() -> str:
    return os.environ[TTS_VOICE_VARIABLE]


def transcription_directory() -> Path:
    return Path(os.environ[TRANSCRIPTION_DIRECTORY_VARIABLE])


def maximum_log_size_bytes() -> int:
    return int(os.environ[MAX_LOG_SIZE_VARIABLE])


def read_gateway_token() -> str:
    token_file = Path(os.environ[GATEWAY_TOKEN_FILE_VARIABLE])
    if not token_file.is_file():
        return ""
    return token_file.read_text(encoding="utf-8").strip()


def gateway_settings() -> GatewaySettings:
    return GatewaySettings(
        url=os.environ[GATEWAY_URL_VARIABLE],
        token=read_gateway_token(),
        agent_id=os.environ[AGENT_ID_VARIABLE],
        model=os.environ[MODEL_VARIABLE],
    )
