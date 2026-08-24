import pytest
from conversation_actions import (
    AnnounceAction,
    ClearWaitContextAction,
    LogTranscriptionAction,
    NotifyAction,
)
from conversation_machine import advance
from conversation_state import ChunkObservation, ConversationMode
from hey_bot_conversation_fixtures import (
    COLLECTING,
    EMPTY_CHUNK,
    FOLLOWING_UP,
    KEYWORD_CHUNK,
    LISTENING,
    LONG_CHUNK,
    SETTINGS,
    SHORT_CHUNK,
    action_types,
)


@pytest.mark.parametrize(
    ("state", "transcription", "expected_mode", "expected_action_types"),
    [
        (LISTENING, EMPTY_CHUNK, ConversationMode.LISTENING, ()),
        (LISTENING, SHORT_CHUNK, ConversationMode.LISTENING, ()),
        (
            LISTENING,
            KEYWORD_CHUNK,
            ConversationMode.COMMAND,
            (AnnounceAction, LogTranscriptionAction, NotifyAction),
        ),
        (LISTENING, LONG_CHUNK, ConversationMode.LISTENING, (LogTranscriptionAction,)),
        (COLLECTING, EMPTY_CHUNK, ConversationMode.COMMAND, ()),
        (COLLECTING, SHORT_CHUNK, ConversationMode.COMMAND, ()),
        (COLLECTING, KEYWORD_CHUNK, ConversationMode.COMMAND, ()),
        (COLLECTING, LONG_CHUNK, ConversationMode.COMMAND, (LogTranscriptionAction,)),
        (FOLLOWING_UP, EMPTY_CHUNK, ConversationMode.FOLLOWUP, ()),
        (FOLLOWING_UP, SHORT_CHUNK, ConversationMode.FOLLOWUP, ()),
        (FOLLOWING_UP, KEYWORD_CHUNK, ConversationMode.FOLLOWUP, ()),
        (
            FOLLOWING_UP,
            LONG_CHUNK,
            ConversationMode.COMMAND,
            (LogTranscriptionAction, AnnounceAction, AnnounceAction, NotifyAction),
        ),
    ],
)
def test_every_state_answers_every_chunk_kind(
    state, transcription, expected_mode, expected_action_types
):
    transition = advance(state, ChunkObservation(transcription), SETTINGS)

    assert transition.state.mode is expected_mode
    assert action_types(transition) == expected_action_types


def test_a_detected_keyword_announces_itself_and_asks_the_user_to_speak():
    transition = advance(LISTENING, ChunkObservation(KEYWORD_CHUNK), SETTINGS)

    assert transition.state.keyword_phrase == KEYWORD_CHUNK
    assert transition.actions == (
        AnnounceAction(f"hey-bot: keyword detected in: '{KEYWORD_CHUNK}'"),
        LogTranscriptionAction(KEYWORD_CHUNK),
        NotifyAction("Listening..."),
    )


def test_a_long_transcription_without_a_keyword_is_only_logged():
    transition = advance(LISTENING, ChunkObservation(LONG_CHUNK), SETTINGS)

    assert transition.actions == (LogTranscriptionAction(LONG_CHUNK),)


def test_the_disabled_flag_file_suppresses_keyword_activation():
    transition = advance(
        LISTENING, ChunkObservation(KEYWORD_CHUNK, keywords_disabled=True), SETTINGS
    )

    assert transition.state.mode is ConversationMode.LISTENING
    assert transition.actions == ()


def test_a_saved_wait_context_is_prepended_to_the_next_keyword_phrase():
    transition = advance(
        LISTENING,
        ChunkObservation(KEYWORD_CHUNK, wait_context="turn on the living room"),
        SETTINGS,
    )

    assert transition.state.keyword_phrase == "turn on the living room hey clever"
    assert ClearWaitContextAction() in transition.actions
    assert (
        AnnounceAction("hey-bot: prepending wait context: 'turn on the living room'")
        in transition.actions
    )
