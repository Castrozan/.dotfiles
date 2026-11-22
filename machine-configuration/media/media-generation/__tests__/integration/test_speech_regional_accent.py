from hypothesis import given
from hypothesis import strategies as st

from media_speech.contract import SUPPORTED_LANGUAGES
from media_speech.delivery import direct_speech_text

NARRATION = st.text(min_size=1).filter(lambda text: text.strip())
DIRECTIONS = st.one_of(
    st.none(),
    st.text(
        st.characters(blacklist_categories=("Cc", "Cs"), blacklist_characters="[]"),
        min_size=1,
        max_size=100,
    ).filter(lambda directions: directions.strip()),
)
PORTUGUESE_LANGUAGES = [
    language for language in SUPPORTED_LANGUAGES if language.split("-")[0] == "pt"
]


@given(narration=NARRATION, directions=DIRECTIONS)
def test_every_portuguese_language_is_spoken_with_a_brazilian_accent_cue(
    narration, directions
):
    assert PORTUGUESE_LANGUAGES
    for language in PORTUGUESE_LANGUAGES:
        spoken = direct_speech_text(
            narration, "elevenlabs", "eleven_v4", directions, language
        )
        cue_group, separator, remainder = spoken.partition("] ")
        assert cue_group.startswith("[")
        assert cue_group.endswith("strong Brazilian Portuguese accent")
        assert (separator + remainder) == "] " + narration


@given(narration=NARRATION, directions=DIRECTIONS)
def test_the_accent_cue_follows_the_delivery_directions_inside_one_tag(
    narration, directions
):
    spoken = direct_speech_text(
        narration, "elevenlabs", "eleven_v4", directions, "pt-br"
    )
    expected_cues = (
        "strong Brazilian Portuguese accent"
        if directions is None
        else f"{directions.strip()}, strong Brazilian Portuguese accent"
    )
    assert spoken == f"[{expected_cues}] {narration}"


@given(
    narration=NARRATION,
    language=st.sampled_from(SUPPORTED_LANGUAGES),
    provider_and_model=st.sampled_from(
        [
            ("kokoro", "kokoro-v1.0-int8-model-files-v1.0"),
            ("elevenlabs", "eleven_multilingual_v2"),
            ("elevenlabs", "eleven_turbo_v2_5"),
            ("elevenlabs", "eleven_flash_v2_5"),
        ]
    ),
)
def test_models_without_audio_tags_never_change_the_narration(
    narration, language, provider_and_model
):
    provider, model = provider_and_model
    assert direct_speech_text(narration, provider, model, None, language) == narration
