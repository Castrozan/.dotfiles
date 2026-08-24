import pytest
from conversation_actions import AnnounceAction, DispatchCommandAction
from conversation_machine import (
    COMMAND_DISPATCHED_MESSAGE,
    EMPTY_COMMAND_MESSAGE,
    FOLLOWUP_DETECTED_MESSAGE,
    FOLLOWUP_WINDOW_ACTIVE_MESSAGE,
    FOLLOWUP_WINDOW_EXPIRED_MESSAGE,
    advance,
)
from conversation_state import ChunkObservation, ConversationMode, ConversationState
from hey_bot_conversation_fixtures import (
    COLLECTING,
    EMPTY_CHUNK,
    FOLLOWING_UP,
    KEYWORD_CHUNK,
    LISTENING,
    SETTINGS,
)


def collecting_state(**overrides):
    return ConversationState(
        mode=ConversationMode.COMMAND, keyword_phrase=KEYWORD_CHUNK, **overrides
    )


def test_a_spoken_chunk_appends_to_the_buffer_and_resets_the_silent_count():
    transition = advance(
        collecting_state(command_buffer=" what is the weather", silent_chunk_count=2),
        ChunkObservation("in florianopolis today"),
        SETTINGS,
    )

    assert transition.state.command_buffer == (
        " what is the weather in florianopolis today"
    )
    assert transition.state.silent_chunk_count == 0
    assert transition.state.command_chunk_count == 1


def test_the_silence_boundary_dispatches_the_whole_phrase():
    transition = advance(
        collecting_state(
            command_buffer=" what is the weather",
            silent_chunk_count=SETTINGS.command_silence_end - 1,
            command_chunk_count=4,
        ),
        ChunkObservation(EMPTY_CHUNK),
        SETTINGS,
    )

    assert transition.state.mode is ConversationMode.LISTENING
    assert transition.actions == (
        AnnounceAction(COMMAND_DISPATCHED_MESSAGE),
        DispatchCommandAction("hey clever what is the weather"),
    )
    assert transition.state.command_buffer == ""
    assert transition.state.keyword_phrase == ""


def test_the_chunk_cap_dispatches_a_command_that_never_falls_silent():
    transition = advance(
        collecting_state(
            command_buffer=" one two three",
            command_chunk_count=SETTINGS.command_max_chunks - 1,
        ),
        ChunkObservation("four five six"),
        SETTINGS,
    )

    assert transition.state.mode is ConversationMode.LISTENING
    assert (
        DispatchCommandAction("hey clever one two three four five six")
        in transition.actions
    )


def test_an_empty_buffer_returns_to_listening_without_dispatching():
    transition = advance(
        collecting_state(silent_chunk_count=SETTINGS.command_silence_end - 1),
        ChunkObservation(EMPTY_CHUNK),
        SETTINGS,
    )

    assert transition.state.mode is ConversationMode.LISTENING
    assert transition.actions == (AnnounceAction(EMPTY_COMMAND_MESSAGE),)


def test_the_followup_signal_opens_the_window_outside_command_mode():
    transition = advance(
        LISTENING, ChunkObservation(EMPTY_CHUNK, followup_signalled=True), SETTINGS
    )

    assert transition.state.mode is ConversationMode.FOLLOWUP
    assert transition.state.followup_chunks_remaining == (
        SETTINGS.followup_window_chunks - 1
    )
    assert AnnounceAction(FOLLOWUP_WINDOW_ACTIVE_MESSAGE) in transition.actions


def test_the_followup_signal_never_interrupts_a_command_being_collected():
    transition = advance(
        COLLECTING, ChunkObservation(EMPTY_CHUNK, followup_signalled=True), SETTINGS
    )

    assert transition.state.mode is ConversationMode.COMMAND
    assert transition.actions == ()


def test_the_followup_window_expires_once_its_budget_runs_out():
    transition = advance(
        ConversationState(mode=ConversationMode.FOLLOWUP, followup_chunks_remaining=1),
        ChunkObservation(EMPTY_CHUNK),
        SETTINGS,
    )

    assert transition.state.mode is ConversationMode.LISTENING
    assert transition.actions == (AnnounceAction(FOLLOWUP_WINDOW_EXPIRED_MESSAGE),)


@pytest.mark.parametrize(
    ("transcription", "expected_mode"),
    [
        ("switch it now", ConversationMode.FOLLOWUP),
        ("please switch it now", ConversationMode.COMMAND),
    ],
)
def test_a_followup_needs_four_words_instead_of_a_keyword(transcription, expected_mode):
    transition = advance(FOLLOWING_UP, ChunkObservation(transcription), SETTINGS)

    assert transition.state.mode is expected_mode
    if expected_mode is ConversationMode.COMMAND:
        assert AnnounceAction(FOLLOWUP_DETECTED_MESSAGE) in transition.actions
        assert transition.state.keyword_phrase == transcription
