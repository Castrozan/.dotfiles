import math
from dataclasses import dataclass
from typing import Protocol


class SpeechError(Exception):
    def __init__(self, category: str):
        self.category = category
        super().__init__(category)


@dataclass(frozen=True)
class SpeechRequest:
    text: str
    voice: str
    language: str

    def __post_init__(self):
        if not self.text.strip() or len(self.text) > 4000:
            raise SpeechError("invalid_text")
        if any(
            ord(character) < 32 and character not in "\n\t" for character in self.text
        ):
            raise SpeechError("invalid_text")
        if self.language not in {"en-us", "pt-br"}:
            raise SpeechError("unsupported_language")
        if not self.voice or len(self.voice) > 100 or not self.voice.isascii():
            raise SpeechError("invalid_voice")
        if not all(character.isalnum() or character == "_" for character in self.voice):
            raise SpeechError("invalid_voice")


@dataclass(frozen=True)
class CharacterAlignment:
    characters: tuple[str, ...]
    starts_seconds: tuple[float, ...]
    ends_seconds: tuple[float, ...]

    def validate(self, duration_seconds: float):
        if not self.characters or len(self.characters) != len(self.starts_seconds):
            raise SpeechError("invalid_alignment")
        if len(self.characters) != len(self.ends_seconds):
            raise SpeechError("invalid_alignment")
        previous_start = 0.0
        previous_end = 0.0
        for character, start, end in zip(
            self.characters, self.starts_seconds, self.ends_seconds, strict=True
        ):
            if not isinstance(character, str) or len(character) != 1:
                raise SpeechError("invalid_alignment")
            if not math.isfinite(start) or not math.isfinite(end):
                raise SpeechError("invalid_alignment")
            if (
                start < previous_start
                or end < previous_end
                or end < start
                or end > duration_seconds + 0.05
            ):
                raise SpeechError("invalid_alignment")
            previous_start = start
            previous_end = end


@dataclass(frozen=True)
class SynthesizedSpeech:
    pcm_audio: bytes
    sample_rate_hz: int
    alignment: CharacterAlignment | None = None
    provider_request_id: str | None = None
    billed_characters: int | None = None


class SpeechProvider(Protocol):
    name: str
    model: str
    requires_payment: bool

    def preflight(self, request: SpeechRequest) -> None: ...

    def synthesize(self, request: SpeechRequest) -> SynthesizedSpeech: ...
