import asyncio
import json
from unittest.mock import AsyncMock, Mock

from voice_bridge import conversation_router
from voice_bridge.conversation_router import ConversationRouter


def test_incomplete_control_request_is_closed_after_bounded_wait(monkeypatch):
    async def scenario():
        async def incomplete_line():
            await asyncio.Future()

        monkeypatch.setattr(
            conversation_router, "CONTROL_REQUEST_DEADLINE_SECONDS", 0.01
        )
        reader = Mock(readline=incomplete_line)
        writer = Mock(drain=AsyncMock(), wait_closed=AsyncMock())
        await ConversationRouter(Mock()).serve_connection(reader, writer)
        assert json.loads(writer.write.call_args.args[0]) == {
            "error": "invalid_request"
        }
        writer.close.assert_called_once()
        writer.wait_closed.assert_awaited_once()

    asyncio.run(scenario())
