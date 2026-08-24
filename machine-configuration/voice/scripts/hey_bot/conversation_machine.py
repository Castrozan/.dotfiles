from __future__ import annotations

import re
from dataclasses import replace

from conversation_actions import (
    AnnounceAction,
    ClearWaitContextAction,
    ConversationAction,
    DispatchCommandAction,
    LogTranscriptionAction,
    NotifyAction,
)
from conversation_state import (
    ChunkObservation,
    ConversationMode,
    ConversationState,
    MachineSettings,
    Transition,
)
from transcription_text import collapse_whitespace, word_count

FOLLOWUP_WINDOW_ACTIVE_MESSAGE = "hey-bot: follow-up window active"
FOLLOWUP_DETECTED_MESSAGE = "hey-bot: follow-up detected"
FOLLOWUP_WINDOW_EXPIRED_MESSAGE = "hey-bot: follow-up window expired"
COMMAND_DISPATCHED_MESSAGE = "hey-bot: sending command to gateway in background"
EMPTY_COMMAND_MESSAGE = "hey-bot: empty command, returning to listening"
LISTENING_NOTIFICATION_BODY = "Listening..."


def advance(
    state: ConversationState,
    observation: ChunkObservation,
    settings: MachineSettings,
) -> Transition:
    actions: list[ConversationAction] = []
    spoken_word_count = word_count(observation.transcription)
    if observation.transcription and spoken_word_count >= settings.logged_word_count:
        actions.append(LogTranscriptionAction(observation.transcription))
    if observation.followup_signalled and state.mode is not ConversationMode.COMMAND:
        state = replace(
            state,
            mode=ConversationMode.FOLLOWUP,
            followup_chunks_remaining=settings.followup_window_chunks,
        )
        actions.append(AnnounceAction(FOLLOWUP_WINDOW_ACTIVE_MESSAGE))
    if state.mode is ConversationMode.COMMAND:
        return collect_command_chunk(state, observation, settings, actions)
    if state.mode is ConversationMode.FOLLOWUP:
        return spend_followup_chunk(
            state, observation, spoken_word_count, settings, actions
        )
    if observation.keywords_disabled:
        return Transition(state, tuple(actions))
    if observation.transcription and matches_keywords(
        observation.transcription, settings
    ):
        return enter_command_mode(
            state, observation, spoken_word_count, settings, actions
        )
    return Transition(state, tuple(actions))


def matches_keywords(transcription: str, settings: MachineSettings) -> bool:
    return (
        re.search(settings.keywords_pattern, transcription, re.IGNORECASE) is not None
    )


def collect_command_chunk(
    state: ConversationState,
    observation: ChunkObservation,
    settings: MachineSettings,
    actions: list[ConversationAction],
) -> Transition:
    if observation.transcription:
        state = replace(
            state,
            command_buffer=f"{state.command_buffer} {observation.transcription}",
            silent_chunk_count=0,
        )
    else:
        state = replace(state, silent_chunk_count=state.silent_chunk_count + 1)
    state = replace(state, command_chunk_count=state.command_chunk_count + 1)
    reached_silence = state.silent_chunk_count >= settings.command_silence_end
    reached_chunk_cap = state.command_chunk_count >= settings.command_max_chunks
    if reached_silence or reached_chunk_cap:
        return dispatch_command(state, actions)
    return Transition(state, tuple(actions))


def dispatch_command(
    state: ConversationState, actions: list[ConversationAction]
) -> Transition:
    if state.command_buffer:
        actions.append(AnnounceAction(COMMAND_DISPATCHED_MESSAGE))
        actions.append(
            DispatchCommandAction(
                collapse_whitespace(f"{state.keyword_phrase} {state.command_buffer}")
            )
        )
    else:
        actions.append(AnnounceAction(EMPTY_COMMAND_MESSAGE))
    return Transition(
        replace(
            state,
            mode=ConversationMode.LISTENING,
            command_buffer="",
            keyword_phrase="",
            silent_chunk_count=0,
            command_chunk_count=0,
        ),
        tuple(actions),
    )


def spend_followup_chunk(
    state: ConversationState,
    observation: ChunkObservation,
    spoken_word_count: int,
    settings: MachineSettings,
    actions: list[ConversationAction],
) -> Transition:
    state = replace(
        state, followup_chunks_remaining=state.followup_chunks_remaining - 1
    )
    promoted = (
        observation.transcription
        and spoken_word_count >= settings.followup_promotion_word_count
    )
    if promoted:
        actions.append(AnnounceAction(FOLLOWUP_DETECTED_MESSAGE))
        state = replace(
            state, mode=ConversationMode.LISTENING, followup_chunks_remaining=0
        )
        return enter_command_mode(
            state, observation, spoken_word_count, settings, actions
        )
    if state.followup_chunks_remaining <= 0:
        state = replace(state, mode=ConversationMode.LISTENING)
        actions.append(AnnounceAction(FOLLOWUP_WINDOW_EXPIRED_MESSAGE))
    return Transition(state, tuple(actions))


def enter_command_mode(
    state: ConversationState,
    observation: ChunkObservation,
    spoken_word_count: int,
    settings: MachineSettings,
    actions: list[ConversationAction],
) -> Transition:
    actions.append(
        AnnounceAction(f"hey-bot: keyword detected in: '{observation.transcription}'")
    )
    if spoken_word_count < settings.logged_word_count:
        actions.append(LogTranscriptionAction(observation.transcription))
    actions.append(NotifyAction(LISTENING_NOTIFICATION_BODY))
    keyword_phrase = observation.transcription
    if observation.wait_context:
        actions.append(ClearWaitContextAction())
        keyword_phrase = f"{observation.wait_context} {observation.transcription}"
        actions.append(
            AnnounceAction(
                f"hey-bot: prepending wait context: '{observation.wait_context}'"
            )
        )
    return Transition(
        replace(
            state,
            mode=ConversationMode.COMMAND,
            command_buffer="",
            keyword_phrase=keyword_phrase,
            silent_chunk_count=0,
            command_chunk_count=0,
        ),
        tuple(actions),
    )
