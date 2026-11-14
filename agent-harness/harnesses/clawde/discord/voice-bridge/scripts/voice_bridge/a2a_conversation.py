import asyncio
import json

from a2a_cli.peer_transport import (
    POLL_INTERVAL_SECONDS,
    TERMINAL_TASK_STATES,
    PeerRequestFailure,
    cancel_task_on_peer,
    peers_matching_target,
    read_task_from_peer,
    resolve_peer_endpoint,
    submit_task_to_peer,
)
from a2a_cli.sender_identity import signed_input_text

from voice_bridge.captured_reply import completed_reply
from voice_bridge.conversation_turn import (
    TURN_DEADLINE_SECONDS,
    ConversationTurnError,
    command_output,
)

DIRECTORY_DEADLINE_SECONDS = 8


async def live_peer(target):
    try:
        directory = json.loads(
            await command_output(["a2a", "list", "--json"], DIRECTORY_DEADLINE_SECONDS)
        )
        resolve_peer_endpoint(directory, target)
        selected = peers_matching_target(directory, target)[0]
        if not selected.get("sessionId") or not selected.get("paneId"):
            raise ConversationTurnError("agent_has_no_verified_session")
        return selected
    except (PeerRequestFailure, ValueError, KeyError, TypeError) as error:
        raise ConversationTurnError("agent_not_resolved") from error


async def peer_request(function, *arguments):
    try:
        return await asyncio.to_thread(function, *arguments)
    except PeerRequestFailure as error:
        raise ConversationTurnError("a2a_request_failed") from error


class A2AConversation:
    def __init__(self, peer, deadline_seconds=TURN_DEADLINE_SECONDS):
        self._peer = peer
        self._deadline_seconds = deadline_seconds

    def status(self):
        return {
            "backend": "a2a",
            "agent": self._peer["name"],
            "pane": self._peer["paneId"],
            "session": self._peer["sessionId"],
            "harness": self._peer["harness"],
        }

    async def reply_to(self, prompt):
        await self._verify_identity()
        task = await self._submitted_task(prompt)
        return await self._reply_to_task(task["id"])

    async def _verify_identity(self):
        current = await live_peer(self._peer["paneId"])
        if any(
            current.get(field) != self._peer.get(field)
            for field in ("paneId", "sessionId", "endpoint")
        ):
            raise ConversationTurnError("agent_identity_changed")

    async def _submitted_task(self, prompt):
        submission = asyncio.create_task(
            peer_request(
                submit_task_to_peer,
                self._peer["endpoint"],
                signed_input_text(prompt, "discord-voice", {}),
            )
        )
        try:
            return await asyncio.shield(submission)
        except asyncio.CancelledError:
            task = await submission
            await self._cancel_task(task["id"])
            raise

    async def _reply_to_task(self, task_identifier):
        try:
            async with asyncio.timeout(self._deadline_seconds):
                return await self._finished_reply(task_identifier)
        except asyncio.CancelledError:
            await self._cancel_task(task_identifier)
            raise
        except (TimeoutError, ConversationTurnError) as error:
            await self._cancel_task(task_identifier)
            reason = (
                "deadline_exceeded" if isinstance(error, TimeoutError) else str(error)
            )
            raise ConversationTurnError(
                f"a2a_task_{task_identifier}_{reason}"
            ) from error

    async def _cancel_task(self, task_identifier):
        try:
            await peer_request(
                cancel_task_on_peer, self._peer["endpoint"], task_identifier
            )
        except ConversationTurnError as error:
            raise ConversationTurnError(
                f"a2a_task_{task_identifier}_cancellation_unconfirmed"
            ) from error

    async def _finished_reply(self, task_identifier):
        while True:
            task = await peer_request(
                read_task_from_peer, self._peer["endpoint"], task_identifier
            )
            if task.get("state") in TERMINAL_TASK_STATES:
                if task["state"] != "completed":
                    raise ConversationTurnError(f"task_{task['state']}")
                return await completed_reply(self._peer, task)
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
