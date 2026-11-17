import dataclasses
import functools
import os
import subprocess
import sys
import time

import conversation_addressee
import conversation_seat
import discord_call
import listener_runtime
import listener_session
import peer_sessions
import remote_agent
import room_holder
import speech_segmenter
from transcription import transcriber
import transcript_log
import wake_claim
import wake_prompts
from servant_panes import live_sessions

MICROPHONE = "@DEFAULT_SOURCE@"
VOICE_SENDER = "voice"
COMMAND_TIMEOUT_SECONDS = 120
PEER_HOSTS_VARIABLE = "AVATAR_PEER_HOSTS"
PEER_HEAD_START_SECONDS = 1.0
PEER_CLAIM_TIMEOUT_SECONDS = 20
FRAME_BYTES = int(speech_segmenter.SAMPLE_RATE * speech_segmenter.FRAME_SECONDS) * 2


def microphone_frames(capture):
    while frame := capture.stdout.read(FRAME_BYTES):
        yield frame


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


def conversation_closed():
    subprocess.run(
        ["avatar-talk", "close"],
        stdout=subprocess.DEVNULL,
        check=False,
        timeout=COMMAND_TIMEOUT_SECONDS,
    )


def transcript_entries():
    return transcript_log.read_since(
        listener_runtime.runtime_directory() / "transcript.jsonl", 0
    )


def prompt_now(pane, text, host=None):
    return (
        subprocess.run(
            remote_agent.on_host(host, ["herdr", "agent", "prompt", pane, text]),
            capture_output=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
        ).returncode
        == 0
    )


def notify_at_idle(pane, text, host=None):
    subprocess.run(
        remote_agent.on_host(
            host, ["a2a", "notify", "--sender", VOICE_SENDER, pane, text]
        ),
        capture_output=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
    )


def claimed_at_the_servant_machine(session, room):
    try:
        return (
            subprocess.run(
                remote_agent.on_host(
                    session.host,
                    ["avatar-wake", "--claim", session.pane, "--room", room],
                ),
                capture_output=True,
                timeout=PEER_CLAIM_TIMEOUT_SECONDS,
            ).returncode
            == 0
        )
    except (OSError, subprocess.TimeoutExpired):
        return False


def claim_wake(session):
    room = wake_prompts.room_name()
    if not session.host:
        return wake_claim.claim(
            listener_runtime.runtime_directory(), session.pane, room, time.time()
        )
    time.sleep(PEER_HEAD_START_SECONDS)
    return claimed_at_the_servant_machine(session, room)


@functools.cache
def peers_of_this_machine():
    return peer_sessions.PeerSessions(
        os.environ.get(PEER_HOSTS_VARIABLE, "").split(), subprocess.run
    )


def sessions_here_and_at_peers():
    return peer_sessions.sessions_everywhere(
        live_sessions(), peers_of_this_machine().known()
    )


def discord_call_at_a_peer():
    return peers_of_this_machine().discord_call_host()


@dataclasses.dataclass
class Boundaries:
    capture_command: object = capture_command
    sessions: object = sessions_here_and_at_peers
    discord_call_host: object = discord_call_at_a_peer
    open_seat: object = lambda: conversation_seat.open_seat(
        listener_runtime.runtime_directory()
    )
    discord_call_ended: object = discord_call.listener_left_the_call
    conversation_listening: object = listener_runtime.listening
    transcribe: object = transcriber.transcribe
    open_conversation: object = conversation_opened
    claim_wake: object = claim_wake
    prompt_now: object = prompt_now
    notify_at_idle: object = notify_at_idle
    transcript_entries: object = transcript_entries
    listening_purpose: object = lambda: listener_session.live_purpose(
        listener_runtime.runtime_directory()
    )
    addressee: object = lambda: conversation_addressee.current(
        listener_runtime.runtime_directory()
    )
    hand_to: object = lambda addressee: room_holder.give_the_room_to(
        listener_runtime.runtime_directory(), addressee
    )
    quiet_seconds: object = lambda: listener_session.quiet_seconds(
        listener_runtime.runtime_directory()
    )
    close_conversation: object = conversation_closed
    report: object = lambda line: print(line, file=sys.stderr, flush=True)
    now: object = time.monotonic
    pause: object = time.sleep


def for_this_machine():
    if sys.platform == "darwin":
        import mac_wake_boundaries

        return Boundaries(**mac_wake_boundaries.mac_boundaries())
    return Boundaries()
