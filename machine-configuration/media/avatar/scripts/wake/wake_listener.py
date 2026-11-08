import argparse
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
from conversation_addressee import Addressee
from wake_phrase import LiveSession, addressed_session, opens_with_greeting

MICROPHONE = "@DEFAULT_SOURCE@"
CONVERSATION_LISTENER = "avatar-listener.service"
ARM_CHECK_SECONDS = 5
FLEET_REFRESH_SECONDS = 60
TRANSCRIPT_POLL_SECONDS = 0.2
FRAME_BYTES = int(speech_segmenter.SAMPLE_RATE * speech_segmenter.FRAME_SECONDS) * 2
FRAMES_PER_ARM_CHECK = int(ARM_CHECK_SECONDS / speech_segmenter.FRAME_SECONDS)
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


def spoken_prompt(message, conversation_open):
    conversation = (
        "The open avatar conversation now listens for you"
        if conversation_open
        else "An avatar conversation is opening"
    )
    return (
        f"[wake] Voice from the room, speaker not verified: {message} "
        f"{conversation}: speak with avatar-talk say, and hear the reply through "
        "avatar-talk follow in a background watcher."
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


class WakeListener:
    def __init__(self, boundaries, dry_run):
        self.boundaries = boundaries
        self.dry_run = dry_run
        self.sessions = []
        self.sessions_read_at = None
        self.conversation_read_through = 0

    def refresh_sessions(self):
        self.sessions = self.boundaries.sessions()
        self.sessions_read_at = self.boundaries.now()

    def armed(self):
        stale = (
            self.sessions_read_at is None
            or self.boundaries.now() - self.sessions_read_at >= FLEET_REFRESH_SECONDS
        )
        if stale:
            self.refresh_sessions()
        return bool(self.sessions) and not self.boundaries.conversation_listening()

    def hear(self, segment):
        try:
            self.answer(segment)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            self.boundaries.report(f"Dropped an utterance: {error}")

    def addressed(self, heard):
        if not opens_with_greeting(heard):
            return None
        self.refresh_sessions()
        return addressed_session(heard, self.sessions)

    def deliver(self, match, conversation_open):
        target = f"{match.session.servant} at {match.session.pane}"
        if self.dry_run:
            self.boundaries.report(f"would wake {target}: {match.message}")
            return False
        self.boundaries.report(f"wake {target}")
        text = spoken_prompt(match.message, conversation_open)
        if not self.boundaries.prompt_now(match.session.pane, text):
            self.boundaries.notify_at_idle(match.session.pane, text)
        return True

    def answer(self, segment):
        heard = self.boundaries.transcribe(segment)
        if not heard:
            return
        match = self.addressed(heard)
        if match is None or not self.deliver(match, conversation_open=False):
            return
        self.boundaries.open_conversation()
        self.boundaries.hand_to(
            Addressee(match.session.pane, match.session.servant, heard_through=0)
        )

    def start_reading_conversation(self):
        entries = self.boundaries.transcript_entries()
        self.conversation_read_through = entries[-1]["sequence"] if entries else 0

    def read_conversation(self):
        entries = self.boundaries.transcript_entries()
        if entries and entries[-1]["sequence"] < self.conversation_read_through:
            self.conversation_read_through = 0
        for entry in entries:
            if entry["sequence"] > self.conversation_read_through:
                self.conversation_read_through = entry["sequence"]
                self.turn_to(entry)

    def turn_to(self, entry):
        match = self.addressed(entry["text"])
        if match is None:
            return
        addressee = self.boundaries.addressee()
        if addressee and addressee.pane == match.session.pane:
            return
        if self.dry_run:
            self.deliver(match, conversation_open=True)
            return
        self.boundaries.hand_to(
            Addressee(match.session.pane, match.session.servant, entry["sequence"])
        )
        self.deliver(match, conversation_open=True)

    def listen_while_armed(self, frames):
        segmenter = speech_segmenter.SpeechSegmenter()
        for count, frame in enumerate(frames, start=1):
            segment = segmenter.feed(frame)
            if segment:
                self.hear(segment)
                return self.armed()
            if count % FRAMES_PER_ARM_CHECK == 0 and not self.armed():
                return False
        return False


def microphone_frames(capture):
    while frame := capture.stdout.read(FRAME_BYTES):
        yield frame


def follow_conversation(wake):
    wake.start_reading_conversation()
    while True:
        check_at = time.monotonic() + ARM_CHECK_SECONDS
        while time.monotonic() < check_at:
            wake.read_conversation()
            time.sleep(TRANSCRIPT_POLL_SECONDS)
        if not wake.boundaries.conversation_listening():
            return


def run(wake):
    while True:
        if wake.boundaries.conversation_listening():
            follow_conversation(wake)
            continue
        if not wake.armed():
            time.sleep(ARM_CHECK_SECONDS)
            continue
        capture = subprocess.Popen(capture_command(), stdout=subprocess.PIPE)
        try:
            while wake.listen_while_armed(microphone_frames(capture)):
                pass
        finally:
            capture.terminate()
            capture.wait()


def main():
    parser = argparse.ArgumentParser(prog="avatar-wake")
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()
    run(WakeListener(Boundaries(), arguments.dry_run))


if __name__ == "__main__":
    main()
