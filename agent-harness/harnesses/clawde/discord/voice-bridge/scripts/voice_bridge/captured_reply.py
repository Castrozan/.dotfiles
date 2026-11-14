import asyncio
import json
import os
import time

from voice_bridge.conversation_turn import ConversationTurnError

CAPTURE_WAIT_SECONDS = 2
CAPTURE_POLL_SECONDS = 0.05


def read_reply_snapshot(peer):
    from herdr_pace.storage.paths import state_directory
    from herdr_pace.storage.replies import MAX_REPLY_BYTES, reply_key

    key = reply_key(peer["paneId"], os.environ["VOICE_CONDUCTOR_HERDR_SOCKET"])
    path = state_directory() / "replies" / f"{key}.json"
    try:
        with path.open("rb") as source:
            return json.loads(source.read(MAX_REPLY_BYTES * 2 + 4096))
    except (OSError, ValueError):
        return None


def capture_matches_task(snapshot, peer, task):
    if not isinstance(snapshot, dict):
        return False
    captured_at = snapshot.get("captured_at")
    if type(captured_at) not in (int, float):
        return False
    return snapshot.get("session_id") == peer["sessionId"] and (
        task["createdAt"] <= captured_at <= task["updatedAt"] + CAPTURE_WAIT_SECONDS
    )


def captured_text(snapshot, peer, task):
    if not capture_matches_task(snapshot, peer, task):
        return None
    text = snapshot.get("text")
    return text if isinstance(text, str) and text.strip() else None


async def completed_reply(peer, task):
    deadline = time.monotonic() + CAPTURE_WAIT_SECONDS
    while True:
        snapshot = await asyncio.to_thread(read_reply_snapshot, peer)
        text = captured_text(snapshot, peer, task)
        if text is not None:
            return text
        if time.monotonic() >= deadline:
            raise ConversationTurnError("completed_reply_unavailable")
        await asyncio.sleep(CAPTURE_POLL_SECONDS)
