from dataclasses import dataclass
from typing import Protocol, AsyncIterator


@dataclass(frozen=True)
class ControlCommand:
    action: str
    payload: dict | None = None


class ControlPort(Protocol):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    def commands(self) -> AsyncIterator[ControlCommand]: ...
    async def send_response(self, data: dict) -> None: ...
