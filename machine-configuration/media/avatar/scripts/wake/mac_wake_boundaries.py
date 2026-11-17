import json
import os
import pathlib
import shlex
import subprocess
import sys
import time

import conversation_addressee
import listener_runtime
import listener_session
import local_seat
import transcript_log
import utterances
from conversation_addressee import Addressee
from listener_session import ListenerPurpose

HOST_ENVIRONMENT_VARIABLE = "AVATAR_AGENT_HOST"
MICROPHONE_PROGRAM = pathlib.Path(__file__).with_name("mac_microphone.py")
REACH_AVATAR_HOST = [
    "ssh",
    "-o",
    "BatchMode=yes",
    "-o",
    "ConnectTimeout=5",
    local_seat.AVATAR_HOST,
]
OPEN_TIMEOUT_SECONDS = 120
FLOOR_TIMEOUT_SECONDS = 60
CONVERSATION_READ_TIMEOUT_SECONDS = 15
CONVERSATION_READ_REUSE_SECONDS = 1


def capture_command():
    return [sys.executable, str(MICROPHONE_PROGRAM)]


def conversation_opened_here():
    return (
        subprocess.run(
            ["avatar-talk", "open"],
            stdout=subprocess.DEVNULL,
            timeout=OPEN_TIMEOUT_SECONDS,
        ).returncode
        == 0
    )


def run_at_the_avatar_host(command, timeout):
    return subprocess.run(
        [*REACH_AVATAR_HOST, shlex.join(command)],
        capture_output=True,
        check=True,
        timeout=timeout,
    ).stdout.decode()


def floor_handed_to(addressee):
    agent = f"{os.environ[HOST_ENVIRONMENT_VARIABLE]}:{addressee.pane}"
    run_at_the_avatar_host(
        [
            "avatar-claim-floor",
            "--agent",
            agent,
            "--heard-through",
            str(addressee.heard_through),
        ],
        FLOOR_TIMEOUT_SECONDS,
    )


def parsed_entries(output):
    return [json.loads(line) for line in output.splitlines() if line.strip()]


class ConversationTranscript:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.entries = []
        self.read_at = None

    def read(self):
        if not local_seat.conversation_listening():
            self.entries = []
            self.read_at = None
            return []
        if self.read_at is not None and (
            self.clock() - self.read_at < CONVERSATION_READ_REUSE_SECONDS
        ):
            return self.entries
        self.read_at = self.clock()
        self.entries = parsed_entries(
            run_at_the_avatar_host(
                ["avatar-listen", "read", "--since", "0"],
                CONVERSATION_READ_TIMEOUT_SECONDS,
            )
        )
        return self.entries


def listening_purpose():
    if not local_seat.conversation_listening():
        return None
    status = json.loads(
        run_at_the_avatar_host(
            ["avatar-listen", "status"], CONVERSATION_READ_TIMEOUT_SECONDS
        )
    )
    purpose = status.get("purpose")
    if not status.get("listening") or purpose not in ListenerPurpose:
        return None
    return ListenerPurpose(purpose)


def addressee_on_this_host():
    if not local_seat.conversation_listening():
        return None
    holder = json.loads(
        run_at_the_avatar_host(
            ["avatar-listen", "addressee"], CONVERSATION_READ_TIMEOUT_SECONDS
        )
    )
    if holder is None:
        return None
    addressee = Addressee(**holder)
    if addressee.host != os.environ[HOST_ENVIRONMENT_VARIABLE]:
        return None
    return addressee


def conversation_listening():
    return listener_runtime.listening() or local_seat.conversation_listening()


def here_or_at_the_host(listening_here, here, at_the_host):
    def chosen(*arguments):
        return (here if listening_here() else at_the_host)(*arguments)

    return chosen


def transcript_here():
    return transcript_log.read_since(
        listener_runtime.runtime_directory() / "transcript.jsonl", 0
    )


def mac_boundaries():
    directory = listener_runtime.runtime_directory()
    listening_here = listener_runtime.listening
    lately_listening_here = utterances.ThrottledCheck(
        listening_here, CONVERSATION_READ_REUSE_SECONDS
    ).passes
    return {
        "capture_command": capture_command,
        "conversation_listening": conversation_listening,
        "open_conversation": conversation_opened_here,
        "transcript_entries": here_or_at_the_host(
            lately_listening_here, transcript_here, ConversationTranscript().read
        ),
        "listening_purpose": here_or_at_the_host(
            listening_here,
            lambda: listener_session.live_purpose(directory),
            listening_purpose,
        ),
        "addressee": here_or_at_the_host(
            listening_here,
            lambda: conversation_addressee.current(directory),
            addressee_on_this_host,
        ),
        "quiet_seconds": here_or_at_the_host(
            listening_here,
            lambda: listener_session.quiet_seconds(directory),
            lambda: 0.0,
        ),
        "hand_to": here_or_at_the_host(
            listening_here,
            lambda addressee: conversation_addressee.hand_to(directory, addressee),
            floor_handed_to,
        ),
    }
