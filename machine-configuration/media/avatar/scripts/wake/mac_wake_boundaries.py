import os
import pathlib
import shlex
import subprocess
import sys

import local_seat
import remote_talk

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
TRANSCRIBE_TIMEOUT_SECONDS = 90
OPEN_TIMEOUT_SECONDS = 120
FLOOR_TIMEOUT_SECONDS = 60


def capture_command():
    return [sys.executable, str(MICROPHONE_PROGRAM)]


def transcribed_at_the_avatar_host(pcm):
    transcript = subprocess.run(
        [*REACH_AVATAR_HOST, "avatar-transcribe"],
        input=pcm,
        capture_output=True,
        check=True,
        timeout=TRANSCRIBE_TIMEOUT_SECONDS,
    )
    return transcript.stdout.decode().strip()


def conversation_opened_here():
    return (
        subprocess.run(
            ["avatar-talk", "open", "--seat", remote_talk.REMOTE_SEAT],
            stdout=subprocess.DEVNULL,
            timeout=OPEN_TIMEOUT_SECONDS,
        ).returncode
        == 0
    )


def floor_handed_to(addressee):
    agent = f"{os.environ[HOST_ENVIRONMENT_VARIABLE]}:{addressee.pane}"
    subprocess.run(
        [*REACH_AVATAR_HOST, shlex.join(["avatar-claim-floor", "--agent", agent])],
        capture_output=True,
        check=True,
        timeout=FLOOR_TIMEOUT_SECONDS,
    )


def mac_boundaries():
    return {
        "capture_command": capture_command,
        "conversation_listening": local_seat.attached,
        "transcribe": transcribed_at_the_avatar_host,
        "open_conversation": conversation_opened_here,
        "transcript_entries": lambda: [],
        "listening_purpose": lambda: None,
        "addressee": lambda: None,
        "hand_to": floor_handed_to,
    }
