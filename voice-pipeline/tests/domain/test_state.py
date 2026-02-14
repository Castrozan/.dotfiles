import pytest

from voice_pipeline.domain.state import (
    PipelineState,
    InvalidTransitionError,
    validate_transition,
)


class TestStateTransitions:
    def test_ambient_to_listening(self):
        validate_transition(PipelineState.AMBIENT, PipelineState.LISTENING)

    def test_listening_to_thinking(self):
        validate_transition(PipelineState.LISTENING, PipelineState.THINKING)

    def test_listening_to_ambient(self):
        validate_transition(PipelineState.LISTENING, PipelineState.AMBIENT)

    def test_thinking_to_speaking(self):
        validate_transition(PipelineState.THINKING, PipelineState.SPEAKING)

    def test_thinking_to_ambient(self):
        validate_transition(PipelineState.THINKING, PipelineState.AMBIENT)

    def test_speaking_to_conversing(self):
        validate_transition(PipelineState.SPEAKING, PipelineState.CONVERSING)

    def test_speaking_to_listening_barge_in(self):
        validate_transition(PipelineState.SPEAKING, PipelineState.LISTENING)

    def test_speaking_to_ambient(self):
        validate_transition(PipelineState.SPEAKING, PipelineState.AMBIENT)

    def test_conversing_to_listening(self):
        validate_transition(PipelineState.CONVERSING, PipelineState.LISTENING)

    def test_conversing_to_ambient(self):
        validate_transition(PipelineState.CONVERSING, PipelineState.AMBIENT)

    def test_invalid_ambient_to_thinking(self):
        with pytest.raises(InvalidTransitionError):
            validate_transition(PipelineState.AMBIENT, PipelineState.THINKING)

    def test_invalid_ambient_to_speaking(self):
        with pytest.raises(InvalidTransitionError):
            validate_transition(PipelineState.AMBIENT, PipelineState.SPEAKING)

    def test_invalid_listening_to_conversing(self):
        with pytest.raises(InvalidTransitionError):
            validate_transition(PipelineState.LISTENING, PipelineState.CONVERSING)

    def test_invalid_thinking_to_listening(self):
        with pytest.raises(InvalidTransitionError):
            validate_transition(PipelineState.THINKING, PipelineState.LISTENING)

    def test_invalid_conversing_to_thinking(self):
        with pytest.raises(InvalidTransitionError):
            validate_transition(PipelineState.CONVERSING, PipelineState.THINKING)
