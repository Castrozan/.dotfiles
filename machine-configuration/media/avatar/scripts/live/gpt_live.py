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


class GptLive:
    name = "gpt-live-1"
    input_rate = RATE
    output_rate = RATE

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
                        "instructions": INSTRUCTIONS,
                        "audio": {
                            "format": {"type": "audio/pcm", "rate": RATE},
                            "output": {"voice": "marin"},
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
            kind = event["type"]
            if kind == "session.output_audio.delta":
                yield Audio(base64.b64decode(event["delta"]))
            elif kind == "session.input_transcript.delta":
                self.user_since_last_task += event["delta"]
                self.recent_user = (self.recent_user + event["delta"])[
                    -RECENT_USER_CHARACTERS:
                ]
                yield UserSaid(event["delta"])
            elif kind == "session.output_transcript.delta":
                yield AssistantSaid(event["delta"])
            elif kind == "session.delegation.created":
                yield TaskRequested(event["delegation"]["id"], self.task_request())
            elif kind in ("session.usage.updated", "session.closed"):
                yield Usage(event.get("usage") or {})
                if kind == "session.closed":
                    return
            elif kind == "error":
                yield Failed(json.dumps(event.get("error")))

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
