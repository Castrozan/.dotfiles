from dataclasses import dataclass, field


@dataclass
class Message:
    role: str
    content: str


class ConversationHistory:
    def __init__(self, max_turns: int = 20) -> None:
        self._max_turns = max_turns
        self._messages: list[Message] = []

    @property
    def messages(self) -> list[Message]:
        return list(self._messages)

    def add_user_message(self, text: str) -> None:
        self._messages.append(Message(role="user", content=text))
        self._trim()

    def add_assistant_message(self, text: str) -> None:
        self._messages.append(Message(role="assistant", content=text))
        self._trim()

    def truncate_last_assistant_message(self, spoken_text: str) -> None:
        for i in range(len(self._messages) - 1, -1, -1):
            if self._messages[i].role == "assistant":
                if spoken_text:
                    self._messages[i] = Message(
                        role="assistant",
                        content=spoken_text + " [interrupted]",
                    )
                else:
                    self._messages.pop(i)
                return

    def clear(self) -> None:
        self._messages.clear()

    def to_api_messages(self, system_prefix: str = "") -> list[dict[str, str]]:
        result = []
        if system_prefix:
            result.append({"role": "system", "content": system_prefix})
        for msg in self._messages:
            result.append({"role": msg.role, "content": msg.content})
        return result

    def _trim(self) -> None:
        max_messages = self._max_turns * 2
        if len(self._messages) > max_messages:
            self._messages = self._messages[-max_messages:]
