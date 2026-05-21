import abc
import dataclasses


@dataclasses.dataclass(frozen=True)
class BackendObservation:
    raw_output_since_last_call: str
    is_alive: bool
    last_activity_at_epoch_seconds: float
    exit_code: int | None = None


class AgentBackend(abc.ABC):
    @abc.abstractmethod
    def start(self) -> None: ...

    @abc.abstractmethod
    def send_input_text(self, text: str) -> None: ...

    @abc.abstractmethod
    def observe(self) -> BackendObservation: ...

    @abc.abstractmethod
    def cancel_gracefully(self) -> None: ...

    @abc.abstractmethod
    def stop(self) -> None: ...
