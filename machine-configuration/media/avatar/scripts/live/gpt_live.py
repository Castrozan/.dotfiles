import base64
import json
from pathlib import Path

import websockets

from live_events import (
    AGENT_CAPABILITIES,
    PERSONA,
    AssistantSaid,
    Audio,
    Failed,
    TaskRequested,
    Usage,
    UserSaid,
)
from live_voice import DEFAULT_VOICE

ENDPOINT = "wss://api.openai.com/v1/live/sessions"
KEY_FILE = Path.home() / ".secrets" / "openai-api-key"
RATE = 24000
RECENT_USER_CHARACTERS = 600

INSTRUCTIONS = f"""{PERSONA}

Backchannel policy: Use light backchannels. Never talk over Lucas while he explains something.

Interruption policy: Stop speaking when Lucas interrupts. Listen to what he says.

Delegation policy:
Backend tools:
- Agent: {AGENT_CAPABILITIES}.

Generate <|SpawnThinking|> when:
- Lucas asks you to do, check, run, find or change anything on his computer or the web.
- A correction changes the work already requested.

Do not generate <|SpawnThinking|> when:
- You can answer from the conversation or a still-current result.
- You need a brief clarification to understand the request.

Generate <|SpawnThinking|> before giving an answer that depends on backend work.
Do not guess the result while waiting. Keep chatting naturally while the agent works."""
EARLIER_CONVERSATION_HEADING = """

You are taking over a conversation already in progress, in a new voice. Carry on from it
without greeting again. The conversation so far, oldest first:
"""


class GptLive:
    name = "gpt-live-1"
    input_rate = RATE
    output_rate = RATE

    def __init__(self, speaking_voice=DEFAULT_VOICE, earlier_conversation=""):
        self.speaking_voice = speaking_voice
        self.instructions = INSTRUCTIONS
        if earlier_conversation:
            self.instructions += EARLIER_CONVERSATION_HEADING + earlier_conversation

    async def connect(self):
        self.socket = await websockets.connect(
            ENDPOINT,
            additional_headers={
                "Authorization": f"Bearer {KEY_FILE.read_text().strip()}"
            },
            max_size=None,
        )
        await self.socket.send(
            json.dumps(
                {
                    "type": "session.start",
                    "session": {
                        "model": "gpt-live-1",
                        "instructions": self.instructions,
                        "audio": {
                            "format": {"type": "audio/pcm", "rate": RATE},
                            "output": {"voice": self.speaking_voice},
                        },
                        "delegation": {"type": "client"},
                    },
                }
            )
        )
        self.user_since_last_task = ""
        self.recent_user = ""
        while True:
            event = json.loads(await self.socket.recv())
            if event["type"] == "session.started":
                return event["session"].get("id")
            if event["type"] == "error":
                raise ConnectionError(event.get("error"))

    async def send_audio(self, pcm):
        await self.socket.send(
            json.dumps(
                {
                    "type": "session.input_audio.append",
                    "audio": base64.b64encode(pcm).decode(),
                }
            )
        )

    def task_request(self):
        request = self.user_since_last_task.strip() or self.recent_user.strip()
        self.user_since_last_task = ""
        return request[-RECENT_USER_CHARACTERS:]

    async def events(self):
        async for message in self.socket:
            event = json.loads(message)
            translate = self.EVENT_TRANSLATIONS.get(event["type"])
            if translate:
                for voice_event in translate(self, event):
                    yield voice_event
            if event["type"] == "session.closed":
                return

    def audio_events(self, event):
        return [Audio(base64.b64decode(event["delta"]))]

    def user_transcript_events(self, event):
        self.user_since_last_task += event["delta"]
        self.recent_user = (self.recent_user + event["delta"])[-RECENT_USER_CHARACTERS:]
        return [UserSaid(event["delta"])]

    def assistant_transcript_events(self, event):
        return [AssistantSaid(event["delta"])]

    def delegation_events(self, event):
        return [TaskRequested(event["delegation"]["id"], self.task_request())]

    def usage_events(self, event):
        return [Usage(event.get("usage") or {})]

    def error_events(self, event):
        return [Failed(json.dumps(event.get("error")))]

    EVENT_TRANSLATIONS = {
        "session.output_audio.delta": audio_events,
        "session.input_transcript.delta": user_transcript_events,
        "session.output_transcript.delta": assistant_transcript_events,
        "session.delegation.created": delegation_events,
        "session.usage.updated": usage_events,
        "session.closed": usage_events,
        "error": error_events,
    }

    async def deliver(self, task_id, result, final):
        kind = "session.commentary.append" if final else "session.thinking.append"
        await self.socket.send(
            json.dumps({"type": kind, "delegation_id": task_id, "content": result})
        )

    async def close(self):
        try:
            await self.socket.send(json.dumps({"type": "session.close"}))
        except websockets.ConnectionClosed:
            pass
