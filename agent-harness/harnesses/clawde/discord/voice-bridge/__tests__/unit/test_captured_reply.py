import asyncio
from unittest.mock import Mock, patch

import pytest
from hypothesis import given, strategies as st

from voice_bridge import captured_reply
from voice_bridge.captured_reply import completed_reply
from voice_bridge.conversation_turn import ConversationTurnError


@given(st.text(min_size=1).filter(lambda text: bool(text.strip())))
def test_completed_native_reply_preserves_text_and_ignores_scraped_output(
    text,
):
    snapshot = {"session_id": "session-1", "captured_at": 12, "text": text}
    task = {
        "createdAt": 10,
        "updatedAt": 13,
        "output": "⏺ obsolete⏺ decorated duplicate",
    }
    with patch.object(captured_reply, "read_reply_snapshot", return_value=snapshot):
        assert asyncio.run(completed_reply({"sessionId": "session-1"}, task)) == text


@pytest.mark.parametrize(
    "snapshot",
    [
        {"session_id": "another-session", "captured_at": 12, "text": "private"},
        {"session_id": "session-1", "captured_at": 9, "text": "stale"},
        {"session_id": "session-1", "captured_at": 99, "text": "later turn"},
        {"session_id": "session-1", "captured_at": 12, "text": ""},
        {"session_id": "session-1", "captured_at": 12, "text": []},
        [],
    ],
)
def test_stale_rotated_missing_or_malformed_capture_is_not_spoken(
    monkeypatch, snapshot
):
    monkeypatch.setattr(
        captured_reply, "read_reply_snapshot", Mock(return_value=snapshot)
    )
    monkeypatch.setattr(captured_reply, "CAPTURE_WAIT_SECONDS", 0)
    with pytest.raises(ConversationTurnError, match="completed_reply_unavailable"):
        asyncio.run(
            completed_reply(
                {"sessionId": "session-1"}, {"createdAt": 10, "updatedAt": 13}
            )
        )


def test_capture_can_arrive_after_a2a_reports_the_turn_finished(monkeypatch):
    snapshots = Mock(
        side_effect=[
            None,
            {"session_id": "session-1", "captured_at": 12, "text": "final"},
        ]
    )
    monkeypatch.setattr(captured_reply, "read_reply_snapshot", snapshots)
    monkeypatch.setattr(captured_reply, "CAPTURE_POLL_SECONDS", 0)
    assert (
        asyncio.run(
            completed_reply(
                {"sessionId": "session-1"}, {"createdAt": 10, "updatedAt": 13}
            )
        )
        == "final"
    )
    assert snapshots.call_count == 2
