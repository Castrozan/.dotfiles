from dataclasses import dataclass, field
from time import time


@dataclass(frozen=True)
class DomainEvent:
    timestamp: float = field(default_factory=time)


@dataclass(frozen=True)
class SpeechStarted(DomainEvent):
    pass


@dataclass(frozen=True)
class SpeechEnded(DomainEvent):
    pass


@dataclass(frozen=True)
class WakeWordDetected(DomainEvent):
    word: str = ""
    transcript: str = ""


@dataclass(frozen=True)
class UtteranceComplete(DomainEvent):
    text: str = ""


@dataclass(frozen=True)
class TranscriptReceived(DomainEvent):
    text: str = ""
    is_final: bool = False


@dataclass(frozen=True)
class CompletionStarted(DomainEvent):
    pass


@dataclass(frozen=True)
class CompletionChunk(DomainEvent):
    text: str = ""


@dataclass(frozen=True)
class CompletionDone(DomainEvent):
    full_text: str = ""


@dataclass(frozen=True)
class SynthesisStarted(DomainEvent):
    pass


@dataclass(frozen=True)
class PlaybackStarted(DomainEvent):
    pass


@dataclass(frozen=True)
class PlaybackDone(DomainEvent):
    pass


@dataclass(frozen=True)
class BargeIn(DomainEvent):
    pass


@dataclass(frozen=True)
class ConversationWindowExpired(DomainEvent):
    pass


@dataclass(frozen=True)
class PipelineToggled(DomainEvent):
    enabled: bool = True


@dataclass(frozen=True)
class AgentSwitched(DomainEvent):
    agent: str = ""
