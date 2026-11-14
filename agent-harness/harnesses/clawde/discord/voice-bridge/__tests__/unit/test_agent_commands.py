import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from voice_bridge import agent_conversations
from voice_bridge.agent_conversations import ConversationTurnError, command_output


@pytest.mark.parametrize("failure", [TimeoutError, asyncio.CancelledError])
def test_interrupted_command_kills_and_reaps_its_process_group(monkeypatch, failure):
    process = Mock(pid=123, returncode=None)
    process.communicate = AsyncMock(side_effect=failure)
    process.wait = AsyncMock()
    monkeypatch.setattr(
        asyncio, "create_subprocess_exec", AsyncMock(return_value=process)
    )
    kill = Mock()
    monkeypatch.setattr(agent_conversations.os, "killpg", kill)
    expected = (
        asyncio.CancelledError
        if failure is asyncio.CancelledError
        else ConversationTurnError
    )
    with pytest.raises(expected):
        asyncio.run(command_output(["agent"]))
    kill.assert_called_once_with(123, agent_conversations.signal.SIGKILL)
    process.wait.assert_awaited_once()


def test_missing_command_is_a_conversation_error(monkeypatch):
    monkeypatch.setattr(
        asyncio, "create_subprocess_exec", AsyncMock(side_effect=FileNotFoundError)
    )
    with pytest.raises(ConversationTurnError, match="unavailable"):
        asyncio.run(command_output(["missing-agent"]))
