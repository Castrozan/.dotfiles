import asyncio
import json
from unittest.mock import AsyncMock

import pytest

from voice_bridge import conversation_router
from voice_bridge.conversation_router import ConversationRouter


class Conversation:
    def status(self):
        return {"backend": "test"}

    async def reply_to(self, prompt):
        return prompt


def test_switching_is_refused_while_the_current_agent_is_replying():
    async def scenario():
        entered = asyncio.Event()
        release = asyncio.Event()

        class BusyConversation(Conversation):
            async def reply_to(self, prompt):
                entered.set()
                await release.wait()
                return prompt

        router = ConversationRouter(BusyConversation())
        replying = asyncio.create_task(router.reply_to("hello"))
        await entered.wait()
        assert await router.answer({"command": "agent", "default": True}) == {
            "error": "agent_busy"
        }
        assert router.status()["busy"] is True
        release.set()
        assert await replying == "hello"
        assert router.status()["busy"] is False

    asyncio.run(scenario())


def test_default_agent_can_be_restored_without_reconnecting_discord(monkeypatch):
    selected = {
        "name": "peer",
        "paneId": "w1:p2",
        "sessionId": "session-1",
        "harness": "claude",
    }
    monkeypatch.setattr(
        conversation_router, "live_peer", AsyncMock(return_value=selected)
    )

    async def scenario():
        router = ConversationRouter(Conversation())
        changed = await router.answer({"command": "agent", "target": "peer"})
        assert changed["backend"] == "a2a"
        assert changed["session"] == "session-1"
        restored = await router.answer({"command": "agent", "default": True})
        assert restored == {"backend": "test", "busy": False}

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "control_request",
    [
        None,
        [],
        {},
        {"command": "invalid"},
        {"command": "agent"},
        {"command": "agent", "target": "x", "default": True},
    ],
)
def test_invalid_control_requests_do_not_change_agent(control_request):
    async def scenario():
        router = ConversationRouter(Conversation())
        assert "error" in await router.answer(control_request)
        assert router.status() == {"backend": "test", "busy": False}

    asyncio.run(scenario())


def test_local_control_socket_round_trip_and_bad_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    async def scenario():
        router = ConversationRouter(Conversation())
        server = await asyncio.start_unix_server(
            router.serve_connection, path="conductor.sock"
        )
        async with server:
            for request in (b'{"command":"status"}\n', b"not json\n"):
                reader, writer = await asyncio.open_unix_connection("conductor.sock")
                writer.write(request)
                await writer.drain()
                reply = json.loads(await reader.readline())
                assert reply == (
                    {"backend": "test", "busy": False}
                    if request.startswith(b"{")
                    else {"error": "invalid_request"}
                )
                writer.close()
                await writer.wait_closed()

    asyncio.run(scenario())
