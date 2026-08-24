from __future__ import annotations

import re
import unicodedata

WHISPER_ARTIFACT_PATTERN = re.compile(
    r"\[BLANK_AUDIO\]|\[silence\]|\[Music\]|\(humming\)|\(singing\)",
    re.IGNORECASE,
)
NON_LATIN_HALLUCINATION_RATIO = 0.3


def collapse_whitespace(text: str) -> str:
    return " ".join(text.split())


def clean_transcription(raw_output: str) -> str:
    return collapse_whitespace(WHISPER_ARTIFACT_PATTERN.sub("", raw_output))


def word_count(text: str) -> int:
    return len(text.split())


def belongs_to_latin_writing(character: str) -> bool:
    if character.isascii():
        return True
    if unicodedata.category(character).startswith("M"):
        return True
    if not character.isalpha():
        return True
    return "LATIN" in unicodedata.name(character, "")


def is_non_latin_hallucination(text: str) -> bool:
    if not text:
        return False
    non_latin_count = sum(
        1 for character in text if not belongs_to_latin_writing(character)
    )
    return non_latin_count > len(text) * NON_LATIN_HALLUCINATION_RATIO
