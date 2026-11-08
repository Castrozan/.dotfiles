import array
import math
from dataclasses import dataclass, field

VOICED_RMS = 500

PERSONA = (
    "You are the avatar's live voice, the spoken front end of the coding agents on Lucas's "
    "computer. He may address an agent by name, such as Suzuka or Voyager: that only picks who "
    "does the work, so answer him yourself. Speak naturally and briefly. Lucas speaks English and "
    "Brazilian Portuguese and may switch mid-conversation: always answer in the language he just "
    "used, with a native accent. When he is clearly talking to someone else in the room, stay silent."
)

AGENT_CAPABILITIES = (
    "a coding agent on Lucas's own computer: it runs shell commands, reads and edits files, "
    "checks the machine, its services and git repositories, and searches the web"
)


@dataclass
class Audio:
    pcm: bytes

    def voiced(self):
        samples = array.array("h", self.pcm[: len(self.pcm) - len(self.pcm) % 2])
        return (
            bool(samples)
            and math.sqrt(sum(s * s for s in samples) / len(samples)) > VOICED_RMS
        )


@dataclass
class UserSaid:
    text: str


@dataclass
class AssistantSaid:
    text: str


@dataclass
class TaskRequested:
    task_id: str
    request: str


@dataclass
class Usage:
    details: dict = field(default_factory=dict)


@dataclass
class Failed:
    message: str
