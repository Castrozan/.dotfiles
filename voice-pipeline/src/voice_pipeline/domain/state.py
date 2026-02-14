from enum import Enum, auto


class PipelineState(Enum):
    AMBIENT = auto()
    LISTENING = auto()
    THINKING = auto()
    SPEAKING = auto()
    CONVERSING = auto()


VALID_TRANSITIONS: dict[PipelineState, set[PipelineState]] = {
    PipelineState.AMBIENT: {PipelineState.LISTENING},
    PipelineState.LISTENING: {PipelineState.THINKING, PipelineState.AMBIENT},
    PipelineState.THINKING: {PipelineState.SPEAKING, PipelineState.AMBIENT},
    PipelineState.SPEAKING: {PipelineState.CONVERSING, PipelineState.LISTENING, PipelineState.AMBIENT},
    PipelineState.CONVERSING: {PipelineState.LISTENING, PipelineState.AMBIENT},
}


class InvalidTransitionError(Exception):
    pass


def validate_transition(current: PipelineState, target: PipelineState) -> None:
    if target not in VALID_TRANSITIONS.get(current, set()):
        raise InvalidTransitionError(f"Cannot transition from {current.name} to {target.name}")
