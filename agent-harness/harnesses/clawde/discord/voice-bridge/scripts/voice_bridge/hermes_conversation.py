import json
from datetime import date

from voice_bridge.conversation_turn import ConversationTurnError, command_output


def result_event_text(line):
    try:
        event = json.loads(line)
    except ValueError:
        return None
    if not isinstance(event, dict) or event.get("type") != "result":
        return None
    text = event.get("text")
    if not isinstance(text, str):
        raise ConversationTurnError("turn_produced_no_result")
    return text


def final_reply_from_turn_events(turn_output):
    for line in reversed(turn_output.splitlines()):
        text = result_event_text(line)
        if text is not None:
            return text
    raise ConversationTurnError("turn_produced_no_result")


class HermesConversation:
    def __init__(self, hermes_executable, profile):
        self._hermes_executable = hermes_executable
        self._profile = profile

    def status(self):
        return {"backend": "hermes", "profile": self._profile}

    async def reply_to(self, prompt):
        output = await command_output(
            [
                self._hermes_executable,
                "-p",
                self._profile,
                "chat",
                "--query",
                prompt,
                "--oneshot",
                "--continue",
                f"voice-call-{date.today().isoformat()}",
                "--create-if-missing",
                "--reasoning",
                "low",
                "--source",
                "tool",
                "--format",
                "stream-json",
            ]
        )
        return final_reply_from_turn_events(output.decode())
