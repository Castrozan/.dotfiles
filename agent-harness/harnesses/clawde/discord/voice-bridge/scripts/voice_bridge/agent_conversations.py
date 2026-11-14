import asyncio
import json
import os
import signal
from datetime import date

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

TURN_DEADLINE_SECONDS = 120
DIRECTORY_DEADLINE_SECONDS = 8


class ConversationTurnError(Exception):
    pass


async def command_output(arguments, deadline_seconds=TURN_DEADLINE_SECONDS):
    try:
        process = await asyncio.create_subprocess_exec(
            *arguments,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as error:
        raise ConversationTurnError("agent_command_unavailable") from error
    try:
        output, _ = await asyncio.wait_for(process.communicate(), deadline_seconds)
    except (TimeoutError, asyncio.CancelledError) as error:
        if process.returncode is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        await process.wait()
        if isinstance(error, asyncio.CancelledError):
            raise
        raise ConversationTurnError("turn_timed_out") from error
    if process.returncode != 0:
        raise ConversationTurnError(f"agent_command_exited_{process.returncode}")
    return output


def final_reply_from_turn_events(turn_output):
    for line in reversed(turn_output.splitlines()):
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("type") == "result":
            text = event.get("text")
            if isinstance(text, str):
                return text
            break
    raise ConversationTurnError("turn_produced_no_result")


class HermesConversation:
    def __init__(self, hermes_executable, profile):
        self._hermes_executable = hermes_executable
        self._profile = profile

    def status(self):
        return {"backend": "hermes", "profile": self._profile}

    async def reply_to(self, prompt):
        output = await command_output(
            [
                self._hermes_executable,
                "-p",
                self._profile,
                "chat",
                "--query",
                prompt,
                "--oneshot",
                "--continue",
                f"voice-call-{date.today().isoformat()}",
                "--create-if-missing",
                "--reasoning",
                "low",
                "--source",
                "tool",
                "--format",
                "stream-json",
            ]
        )
        return final_reply_from_turn_events(output.decode())


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
        current = await live_peer(self._peer["paneId"])
        if any(
            current.get(field) != self._peer.get(field)
            for field in ("paneId", "sessionId", "endpoint")
        ):
            raise ConversationTurnError("agent_identity_changed")
        endpoint = self._peer["endpoint"]
        task = await peer_request(
            submit_task_to_peer,
            endpoint,
            signed_input_text(prompt, "discord-voice", {}),
        )
        task_identifier = task["id"]
        try:
            async with asyncio.timeout(self._deadline_seconds):
                return await self._finished_reply(endpoint, task_identifier)
        except (TimeoutError, asyncio.CancelledError, ConversationTurnError) as error:
            try:
                await peer_request(cancel_task_on_peer, endpoint, task_identifier)
            except ConversationTurnError as cancellation_error:
                raise ConversationTurnError(
                    f"a2a_task_{task_identifier}_cancellation_unconfirmed"
                ) from cancellation_error
            if isinstance(error, asyncio.CancelledError):
                raise
            raise ConversationTurnError(
                f"a2a_task_{task_identifier}_{error}"
            ) from error

    async def _finished_reply(self, endpoint, task_identifier):
        while True:
            task = await peer_request(read_task_from_peer, endpoint, task_identifier)
            if task.get("state") in TERMINAL_TASK_STATES:
                if task["state"] != "completed":
                    raise ConversationTurnError(f"task_{task['state']}")
                output = task.get("output")
                if not isinstance(output, str):
                    raise ConversationTurnError("task_has_no_text_output")
                return output
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
