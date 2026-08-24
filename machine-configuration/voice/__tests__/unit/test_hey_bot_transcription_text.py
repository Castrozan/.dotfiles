import pytest
from hey_bot.transcription_text import (
    clean_transcription,
    collapse_whitespace,
    is_non_latin_hallucination,
    word_count,
)


@pytest.mark.parametrize(
    ("raw_output", "expected"),
    [
        ("  hello there  \n", "hello there"),
        ("hello\nthere\n", "hello there"),
        ("[BLANK_AUDIO]", ""),
        ("hello [Music] there", "hello there"),
        ("[silence] hello (humming) there (singing)", "hello there"),
    ],
)
def test_whisper_artifacts_and_ragged_spacing_leave_the_transcription(
    raw_output, expected
):
    assert clean_transcription(raw_output) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", False),
        ("the coffee machine is running", False),
        ("qual a previsão do tempo hoje", False),
        ("こんにちは 世界 元気ですか", True),
        ("привет как дела сегодня", True),
    ],
)
def test_a_mostly_non_latin_transcription_reads_as_a_hallucination(text, expected):
    assert is_non_latin_hallucination(text) is expected


def test_word_count_follows_whitespace_separated_words():
    assert word_count("") == 0
    assert word_count("  hey   clever  ") == 2


def test_collapse_whitespace_squeezes_and_trims():
    assert collapse_whitespace("  hey   clever  now ") == "hey clever now"
