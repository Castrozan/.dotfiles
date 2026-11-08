import dataclasses
import subprocess
import sys
import time

import conversation_addressee
import listener
import speech_segmenter
import transcriber
import transcript_log
import user_units
from a2a_cli import peer_identity
from wake_phrase import LiveSession

MICROPHONE = "@DEFAULT_SOURCE@"
CONVERSATION_LISTENER = "avatar-listener.service"
VOICE_SENDER = "voice"
COMMAND_TIMEOUT_SECONDS = 120


def capture_command():
    return [
        "parec",
        f"--device={MICROPHONE}",
        "--client-name=avatar-wake",
        "--raw",
        "--format=s16le",
        f"--rate={speech_segmenter.SAMPLE_RATE}",
        "--channels=1",
        "--latency-msec=100",
    ]


def live_sessions():
    sessions = []
    for pane in peer_identity.read_live_panes():
        servant = peer_identity.identity_of_pane(pane).get("servant")
        if servant:
            sessions.append(LiveSession(servant=servant, pane=pane["pane_id"]))
    return sessions


def conversation_opened():
    return (
        subprocess.run(
            ["avatar-talk", "open"],
            stdout=subprocess.DEVNULL,
            timeout=COMMAND_TIMEOUT_SECONDS,
        ).returncode
        == 0
    )


def transcript_entries():
    return transcript_log.read_since(
        listener.runtime_directory() / "transcript.jsonl", 0
    )


def prompt_now(pane, text):
    return (
        subprocess.run(
            ["herdr", "agent", "prompt", pane, text],
            capture_output=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
        ).returncode
        == 0
    )


def notify_at_idle(pane, text):
    subprocess.run(
        ["a2a", "notify", "--sender", VOICE_SENDER, pane, text],
        capture_output=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
    )


@dataclasses.dataclass
class Boundaries:
    sessions: object = live_sessions
    conversation_listening: object = lambda: user_units.unit_active(
        CONVERSATION_LISTENER
    )
    transcribe: object = transcriber.transcribe
    open_conversation: object = conversation_opened
    prompt_now: object = prompt_now
    notify_at_idle: object = notify_at_idle
    transcript_entries: object = transcript_entries
    addressee: object = lambda: conversation_addressee.current(
        listener.runtime_directory()
    )
    hand_to: object = lambda addressee: conversation_addressee.hand_to(
        listener.runtime_directory(), addressee
    )
    report: object = lambda line: print(line, file=sys.stderr, flush=True)
    now: object = time.monotonic
