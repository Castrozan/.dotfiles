from dataclasses import dataclass
from typing import Protocol, AsyncIterator


@dataclass(frozen=True)
class TranscriptEvent:
    text: str
    is_final: bool


class TranscriberPort(Protocol):
    async def start_session(self) -> None: ...
    async def send_audio(self, frame: bytes) -> None: ...
    def get_transcripts(self) -> AsyncIterator[TranscriptEvent]: ...
    async def close_session(self) -> None: ...
