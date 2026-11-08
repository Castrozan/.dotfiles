import dataclasses
import subprocess
import sys
import time

import conversation_addressee
import listener
import listener_session
import speech_segmenter
import transcriber
import transcript_log
import user_units
from servant_panes import live_sessions

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
    listening_purpose: object = lambda: listener_session.live_purpose(
        listener.runtime_directory()
    )
    addressee: object = lambda: conversation_addressee.current(
        listener.runtime_directory()
    )
    hand_to: object = lambda addressee: conversation_addressee.hand_to(
        listener.runtime_directory(), addressee
    )
    report: object = lambda line: print(line, file=sys.stderr, flush=True)
    now: object = time.monotonic
