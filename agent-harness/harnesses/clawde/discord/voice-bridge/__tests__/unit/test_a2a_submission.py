import asyncio

import pytest

from voice_bridge import agent_conversations
from voice_bridge.agent_conversations import A2AConversation


def test_cancellation_during_submission_waits_for_receipt_then_cancels_exact_task(
    monkeypatch,
):
    async def scenario():
        selected = {
            "name": "peer",
            "paneId": "w1:p2",
            "sessionId": "session-1",
            "endpoint": "http://peer",
            "harness": "claude",
        }
        entered = asyncio.Event()
        release = asyncio.Event()
        requests = []

        async def live_peer(_target):
            return selected

        async def request(function, *arguments):
            requests.append((function.__name__, arguments))
            if function.__name__ == "submit_task_to_peer":
                entered.set()
                await release.wait()
                return {"id": "receipt-after-cancellation"}
            return {"state": "canceled"}

        monkeypatch.setattr(agent_conversations, "live_peer", live_peer)
        monkeypatch.setattr(agent_conversations, "peer_request", request)
        replying = asyncio.create_task(A2AConversation(selected).reply_to("hello"))
        await entered.wait()
        replying.cancel()
        await asyncio.sleep(0)
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await replying
        assert requests[-1] == (
            "cancel_task_on_peer",
            ("http://peer", "receipt-after-cancellation"),
        )

    asyncio.run(scenario())
