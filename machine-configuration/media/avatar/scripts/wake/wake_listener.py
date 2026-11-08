import argparse
import dataclasses
import subprocess
import sys
import time

import speech_segmenter
import transcriber
import user_units
from a2a_cli import peer_identity
from wake_phrase import LiveSession, addressed_session

MICROPHONE = "@DEFAULT_SOURCE@"
CONVERSATION_LISTENER = "avatar-listener.service"
ARM_CHECK_SECONDS = 5
FLEET_REFRESH_SECONDS = 60
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
    prompt = f"[wake] Voice from the room, speaker not verified: {message}"
    if conversation_open:
        return f"{prompt} An avatar conversation is open; answer with avatar-talk ask."
    return prompt


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
    report: object = lambda line: print(line, file=sys.stderr, flush=True)
    now: object = time.monotonic


class WakeListener:
    def __init__(self, boundaries, dry_run):
        self.boundaries = boundaries
        self.dry_run = dry_run
        self.sessions = []
        self.sessions_read_at = None

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

    def answer(self, segment):
        heard = self.boundaries.transcribe(segment)
        if not heard:
            return
        self.refresh_sessions()
        match = addressed_session(heard, self.sessions)
        if match is None:
            return
        target = f"{match.session.servant} at {match.session.pane}"
        if self.dry_run:
            self.boundaries.report(f"would wake {target}: {match.message}")
            return
        self.boundaries.report(f"wake {target}")
        text = spoken_prompt(match.message, self.boundaries.open_conversation())
        if not self.boundaries.prompt_now(match.session.pane, text):
            self.boundaries.notify_at_idle(match.session.pane, text)

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


def run(listener):
    while True:
        if not listener.armed():
            time.sleep(ARM_CHECK_SECONDS)
            continue
        capture = subprocess.Popen(capture_command(), stdout=subprocess.PIPE)
        try:
            while listener.listen_while_armed(microphone_frames(capture)):
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
