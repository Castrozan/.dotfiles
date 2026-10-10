"""Normalize bounded trailing separator timestamps from ElevenLabs."""

import unicodedata

from media_speech.contract import CharacterAlignment, SpeechError


def trailing_boundary(characters):
    boundary = len(characters)
    for character in reversed(characters):
        if not (character.isspace() or unicodedata.category(character).startswith("P")):
            break
        boundary -= 1
    return boundary


def clamp_separators(alignment, duration, indices):
    starts = list(alignment.starts_seconds)
    ends = list(alignment.ends_seconds)
    adjustments = []
    for index in indices:
        adjustments.append(
            {
                "index": index,
                "original_start_seconds": starts[index],
                "original_end_seconds": ends[index],
                "reason": "trailing_separator_past_audio_end",
            }
        )
        starts[index], ends[index] = min(starts[index], duration), duration
    return CharacterAlignment(alignment.characters, tuple(starts), tuple(ends)), tuple(
        adjustments
    )


def normalize_trailing_separators(alignment, duration):
    if alignment is None:
        return None, ()
    try:
        alignment.validate(float("inf"))
    except SpeechError:
        return alignment, ()
    boundary = trailing_boundary(alignment.characters)
    indices = [
        index
        for index in range(boundary, len(alignment.characters))
        if alignment.ends_seconds[index] > duration
    ]
    if any(alignment.ends_seconds[index] - duration > 0.1 for index in indices):
        return alignment, ()
    return clamp_separators(alignment, duration, indices)
