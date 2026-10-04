from dataclasses import dataclass
from typing import Protocol

from media_speech.contract import (
    MAXIMUM_TEXT_CHARACTERS,
    SUPPORTED_LANGUAGES,
    SpeechError,
    validate_voice_identifier,
)


@dataclass(frozen=True)
class SpeechCapabilities:
    provider: str
    model: str
    execution: str
    requires_payment: bool
    requires_credentials: bool
    alignment: str
    language_enforcement: bool
    voice_catalog: str
    languages: tuple[str, ...] = SUPPORTED_LANGUAGES
    maximum_text_characters: int = MAXIMUM_TEXT_CHARACTERS


@dataclass(frozen=True)
class VoiceQuery:
    page_size: int = 20
    page_token: str | None = None
    search: str | None = None

    def __post_init__(self):
        if not 1 <= self.page_size <= 100:
            raise SpeechError("invalid_page_size")
        if self.page_token is not None and (
            not self.page_token or len(self.page_token) > 4096
        ):
            raise SpeechError("invalid_page_token")
        if self.search is not None and (
            not self.search.strip() or len(self.search) > 200
        ):
            raise SpeechError("invalid_voice_search")


@dataclass(frozen=True)
class SpeechVoice:
    voice_id: str
    name: str
    language: str | None = None
    preview_url: str | None = None

    def __post_init__(self):
        validate_voice_identifier(self.voice_id)
        if (
            not isinstance(self.name, str)
            or not self.name
            or (self.language is not None and self.language not in SUPPORTED_LANGUAGES)
            or (self.preview_url is not None and not isinstance(self.preview_url, str))
        ):
            raise SpeechError("invalid_voice_descriptor")


@dataclass(frozen=True)
class SpeechVoicePage:
    voices: tuple[SpeechVoice, ...]
    next_page_token: str | None


class SpeechVoiceCatalog(Protocol):
    def list_voices(self, query: VoiceQuery) -> SpeechVoicePage: ...
