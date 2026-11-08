import argparse
import dataclasses
import subprocess
import sys
import time

import speech_segmenter
import transcriber
import user_units
from wake_phrase import LiveSession, addressed_session

MICROPHONE = "@DEFAULT_SOURCE@"
CONVERSATION_LISTENER = "avatar-listener.service"
ARM_CHECK_SECONDS = 5
FRAME_BYTES = int(speech_segmenter.SAMPLE_RATE * speech_segmenter.FRAME_SECONDS) * 2
FRAMES_PER_ARM_CHECK = int(ARM_CHECK_SECONDS / speech_segmenter.FRAME_SECONDS)
NO_SERVANT = "-"
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
    listing = subprocess.run(
        ["a2a", "list"], capture_output=True, text=True, timeout=COMMAND_TIMEOUT_SECONDS
    )
    sessions = []
    for line in listing.stdout.splitlines():
        columns = line.split("\t")
        if len(columns) >= 4 and columns[1] != NO_SERVANT:
            sessions.append(LiveSession(servant=columns[1], pane=columns[3]))
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
    prompt = f"[wake] Lucas said by voice: {message}"
    if conversation_open:
        return (
            f"{prompt} An avatar conversation is open; answer him with avatar-talk ask."
        )
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


class WakeListener:
    def __init__(self, boundaries, dry_run):
        self.boundaries = boundaries
        self.dry_run = dry_run
        self.sessions = []

    def armed(self):
        self.sessions = self.boundaries.sessions()
        return bool(self.sessions) and not self.boundaries.conversation_listening()

    def hear(self, segment):
        match = addressed_session(self.boundaries.transcribe(segment), self.sessions)
        if match is None:
            return
        if self.dry_run:
            self.boundaries.report(
                f"would wake {match.session.servant} at {match.session.pane}: {match.message}"
            )
            return
        self.boundaries.report(f"wake {match.session.servant} at {match.session.pane}")
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
