import asyncio
import json

from voice_bridge.a2a_conversation import A2AConversation, live_peer
from voice_bridge.conversation_turn import ConversationTurnError

CONTROL_REQUEST_DEADLINE_SECONDS = 5


def selected_target(request):
    target = request.get("target")
    use_default = request.get("default") is True
    if use_default == bool(target) or (
        target is not None and not isinstance(target, str)
    ):
        raise ConversationTurnError("choose_target_or_default")
    return None if use_default else target


class ConversationRouter:
    def __init__(self, default_conversation):
        self._default_conversation = default_conversation
        self._conversation = default_conversation
        self._turn_lock = asyncio.Lock()
        self._handlers = {"status": self._answer_status, "agent": self._select_agent}

    def status(self):
        return {**self._conversation.status(), "busy": self._turn_lock.locked()}

    async def reply_to(self, prompt):
        async with self._turn_lock:
            return await self._conversation.reply_to(prompt)

    async def answer(self, request):
        if not isinstance(request, dict):
            return {"error": "invalid_request"}
        command = request.get("command")
        if not isinstance(command, str):
            return {"error": "unknown_command"}
        handler = self._handlers.get(command)
        if handler is None:
            return {"error": "unknown_command"}
        return await handler(request)

    async def _answer_status(self, _request):
        return self.status()

    async def _select_agent(self, request):
        try:
            target = selected_target(request)
        except ConversationTurnError as error:
            return {"error": str(error)}
        if self._turn_lock.locked():
            return {"error": "agent_busy"}
        async with self._turn_lock:
            try:
                conversation = (
                    self._default_conversation
                    if target is None
                    else A2AConversation(await live_peer(target))
                )
            except ConversationTurnError as error:
                return {"error": str(error)}
            self._conversation = conversation
        return self.status()

    async def serve_connection(self, reader, writer):
        try:
            try:
                request = json.loads(
                    await asyncio.wait_for(
                        reader.readline(), CONTROL_REQUEST_DEADLINE_SECONDS
                    )
                )
                reply = await self.answer(request)
            except (ValueError, UnicodeDecodeError, TimeoutError):
                reply = {"error": "invalid_request"}
            writer.write(json.dumps(reply).encode() + b"\n")
            await writer.drain()
        except ConnectionError:
            pass
        finally:
            writer.close()
            await writer.wait_closed()
