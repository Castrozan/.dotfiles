import asyncio
import json
from unittest.mock import AsyncMock

import pytest
from hypothesis import given, strategies as st

from voice_bridge import agent_conversations
from voice_bridge.agent_conversations import (
    A2AConversation,
    ConversationTurnError,
    HermesConversation,
    final_reply_from_turn_events,
)


@given(st.text())
def test_hermes_result_preserves_arbitrary_reply_text(text):
    output = json.dumps({"type": "result", "text": text}) + "\nsession_id: trailer"
    assert final_reply_from_turn_events(output) == text


@pytest.mark.parametrize("result", [None, 1, [], {}, {"type": "result", "text": []}])
def test_invalid_results_are_rejected(result):
    with pytest.raises(ConversationTurnError):
        final_reply_from_turn_events(json.dumps(result))


def test_hermes_keeps_explicit_profile_and_daily_session(monkeypatch):
    command = AsyncMock(return_value=b'{"type":"result","text":"Hello."}')
    monkeypatch.setattr(agent_conversations, "command_output", command)
    conversation = HermesConversation("/bin/hermes", "silver")
    assert asyncio.run(conversation.reply_to("hello")) == "Hello."
    arguments = command.call_args.args[0]
    assert arguments[:5] == ["/bin/hermes", "-p", "silver", "chat", "--query"]
    assert arguments[5] == "hello"
    assert "--oneshot" in arguments
    assert arguments[arguments.index("--continue") + 1].startswith("voice-call-")


def peer(session="conversation-1"):
    return {
        "name": "work-peer",
        "paneId": "w1:p2",
        "sessionId": session,
        "harness": "claude",
        "endpoint": "http://127.0.0.1:7000/agents/work-peer",
    }


def test_a2a_uses_task_output_only_after_terminal_success(monkeypatch):
    selected = peer()
    monkeypatch.setattr(
        agent_conversations, "live_peer", AsyncMock(return_value=selected)
    )
    submit = AsyncMock(return_value={"id": "task-1"})
    read = AsyncMock(
        side_effect=[{"state": "working"}, {"state": "completed", "output": "Hello."}]
    )
    cancel = AsyncMock()

    async def request(function, *arguments):
        handler = {
            "submit_task_to_peer": submit,
            "read_task_from_peer": read,
            "cancel_task_on_peer": cancel,
        }[function.__name__]
        return await handler(*arguments)

    monkeypatch.setattr(agent_conversations, "peer_request", request)
    monkeypatch.setattr(agent_conversations, "POLL_INTERVAL_SECONDS", 0)
    assert asyncio.run(A2AConversation(selected).reply_to("hello")) == "Hello."
    assert read.await_count == 2
    assert submit.call_args.args[1].endswith(" — discord-voice")
    cancel.assert_not_called()


def test_a_rotated_peer_is_not_given_the_previous_conversations_speech(monkeypatch):
    monkeypatch.setattr(
        agent_conversations, "live_peer", AsyncMock(return_value=peer("new-session"))
    )
    request = AsyncMock()
    monkeypatch.setattr(agent_conversations, "peer_request", request)
    with pytest.raises(ConversationTurnError, match="agent_identity_changed"):
        asyncio.run(A2AConversation(peer()).reply_to("private speech"))
    request.assert_not_called()


def test_a2a_cancels_the_exact_task_on_deadline(monkeypatch):
    selected = peer()
    monkeypatch.setattr(
        agent_conversations, "live_peer", AsyncMock(return_value=selected)
    )
    requests = []

    async def request(function, *arguments):
        requests.append((function.__name__, arguments))
        if function.__name__ == "submit_task_to_peer":
            return {"id": "task-exact"}
        if function.__name__ == "cancel_task_on_peer":
            return {"state": "canceled"}
        await asyncio.sleep(10)

    monkeypatch.setattr(agent_conversations, "peer_request", request)
    with pytest.raises(ConversationTurnError, match="task-exact"):
        asyncio.run(A2AConversation(selected, deadline_seconds=0.01).reply_to("hello"))
    assert requests[-1] == ("cancel_task_on_peer", (selected["endpoint"], "task-exact"))


def test_a2a_failed_task_does_not_speak_partial_output(monkeypatch):
    selected = peer()
    monkeypatch.setattr(
        agent_conversations, "live_peer", AsyncMock(return_value=selected)
    )

    async def request(function, *arguments):
        if function.__name__ == "submit_task_to_peer":
            return {"id": "task-failed"}
        return {"state": "failed", "output": "partial"}

    monkeypatch.setattr(agent_conversations, "peer_request", request)
    with pytest.raises(ConversationTurnError, match="failed"):
        asyncio.run(A2AConversation(selected).reply_to("hello"))
