import pytest

from media_speech.contract import CharacterAlignment, SpeechError
from media_speech.elevenlabs_alignment import normalize_trailing_separators


def test_provider_tail_punctuation_is_clamped_without_changing_spoken_characters():
    original = CharacterAlignment(
        ("e", ".", "\n"), (46.48, 46.56, 46.96), (46.56, 46.96, 46.96)
    )
    aligned, adjustments = normalize_trailing_separators(original, 46.88)
    aligned.validate(46.88)
    assert aligned.starts_seconds == (46.48, 46.56, 46.88)
    assert aligned.ends_seconds == (46.56, 46.88, 46.88)
    assert [item["index"] for item in adjustments] == [1, 2]
    assert adjustments[0]["original_end_seconds"] == 46.96


@pytest.mark.parametrize(
    "alignment",
    [
        CharacterAlignment(("e",), (0.8,), (1.08,)),
        CharacterAlignment((".",), (0.8,), (1.2,)),
        CharacterAlignment((".", "e"), (0.8, 0.9), (1.08, 1.1)),
        CharacterAlignment((".",), (1.08,), (0.9,)),
        CharacterAlignment((".",), (float("nan"),), (1.08,)),
        CharacterAlignment((".",), (), (1.08,)),
    ],
)
def test_invalid_speech_or_unbounded_alignment_is_still_rejected(alignment):
    aligned, adjustments = normalize_trailing_separators(alignment, 1.0)
    with pytest.raises(SpeechError, match="invalid_alignment"):
        aligned.validate(1.0)


def test_missing_alignment_remains_unavailable():
    assert normalize_trailing_separators(None, 1.0) == (None, ())
