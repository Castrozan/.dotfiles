from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from hey_bot.conversation_actions import ConversationAction

COMMAND_MAX_CHUNKS = 15
COMMAND_SILENCE_END = 3
FOLLOWUP_WINDOW_CHUNKS = 5
LOGGED_WORD_COUNT = 3
FOLLOWUP_PROMOTION_WORD_COUNT = 4


class ConversationMode(Enum):
    LISTENING = auto()
    COMMAND = auto()
    FOLLOWUP = auto()


@dataclass(frozen=True)
class MachineSettings:
    keywords_pattern: str
    command_max_chunks: int = COMMAND_MAX_CHUNKS
    command_silence_end: int = COMMAND_SILENCE_END
    followup_window_chunks: int = FOLLOWUP_WINDOW_CHUNKS
    logged_word_count: int = LOGGED_WORD_COUNT
    followup_promotion_word_count: int = FOLLOWUP_PROMOTION_WORD_COUNT


@dataclass(frozen=True)
class ConversationState:
    mode: ConversationMode = ConversationMode.LISTENING
    command_buffer: str = ""
    keyword_phrase: str = ""
    silent_chunk_count: int = 0
    command_chunk_count: int = 0
    followup_chunks_remaining: int = 0


@dataclass(frozen=True)
class ChunkObservation:
    transcription: str = ""
    followup_signalled: bool = False
    keywords_disabled: bool = False
    wait_context: str = ""


@dataclass(frozen=True)
class Transition:
    state: ConversationState
    actions: tuple[ConversationAction, ...]
