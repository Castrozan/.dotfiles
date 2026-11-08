import argparse
import subprocess
import time

import speech_segmenter
from conversation_addressee import Addressee
from listener_session import ListenerPurpose
from wake_boundaries import Boundaries, capture_command
from wake_phrase import addressed_session, named_in_turn, opens_with_greeting

ARM_CHECK_SECONDS = 5
FLEET_REFRESH_SECONDS = 60
TRANSCRIPT_POLL_SECONDS = 0.2
FRAME_BYTES = int(speech_segmenter.SAMPLE_RATE * speech_segmenter.FRAME_SECONDS) * 2
FRAMES_PER_ARM_CHECK = int(ARM_CHECK_SECONDS / speech_segmenter.FRAME_SECONDS)


DESK_REPLY = (
    "speak with avatar-talk say, and hear the reply through avatar-talk follow in a "
    "background watcher. When the room dismisses you, such as 'you can go now', say "
    "a short goodbye and run avatar-talk close, which hands the room back to the wake."
)
SETTINGS = {
    None: f"An avatar conversation is opening: {DESK_REPLY}",
    ListenerPurpose.CONVERSATION: (
        f"The open avatar conversation now listens for you: {DESK_REPLY}"
    ),
    ListenerPurpose.MEETING: (
        "You now hold the floor of the meeting the avatar transcribes: answer aloud "
        "with avatar-command speak, which the meeting hears, and read it through "
        "avatar-listen follow in a background watcher."
    ),
}
MEETING_SOURCE = "meeting"
AVATAR = "avatar"


def spoken_prompt(message, purpose):
    return (
        f"[wake] Voice from the room, speaker not verified: {message} "
        f"{SETTINGS[purpose]}"
    )


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

    def sessions_stale(self):
        return (
            self.sessions_read_at is None
            or self.boundaries.now() - self.sessions_read_at >= FLEET_REFRESH_SECONDS
        )

    def armed(self):
        if self.sessions_stale():
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

    def deliver(self, match, purpose):
        target = f"{match.session.servant} at {match.session.pane}"
        if self.dry_run:
            self.boundaries.report(f"would wake {target}: {match.message}")
            return False
        self.boundaries.report(f"wake {target}")
        text = spoken_prompt(match.message, purpose)
        if not self.boundaries.prompt_now(match.session.pane, text):
            self.boundaries.notify_at_idle(match.session.pane, text)
        return True

    def answer(self, segment):
        heard = self.boundaries.transcribe(segment)
        if not heard:
            return
        match = self.addressed(heard)
        if match is None or not self.deliver(match, purpose=None):
            return
        self.boundaries.open_conversation()
        self.boundaries.hand_to(
            Addressee(match.session.pane, match.session.servant, heard_through=0)
        )

    def start_reading_conversation(self):
        entries = self.boundaries.transcript_entries()
        self.conversation_read_through = entries[-1]["sequence"] if entries else 0

    def read_conversation(self):
        try:
            self.turn_on_new_entries()
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            self.boundaries.report(f"Dropped a conversation turn: {error}")

    def turn_on_new_entries(self):
        entries = self.boundaries.transcript_entries()
        if entries and entries[-1]["sequence"] < self.conversation_read_through:
            self.conversation_read_through = 0
        for entry in entries:
            if entry["sequence"] > self.conversation_read_through:
                self.conversation_read_through = entry["sequence"]
                self.turn_to(entry)

    def named_in_conversation(self, text):
        if opens_with_greeting(text) or self.sessions_stale():
            self.refresh_sessions()
        return named_in_turn(text, self.sessions)

    def turn_to(self, entry):
        if entry.get("source") == MEETING_SOURCE or entry.get("speaker") == AVATAR:
            return
        match = self.named_in_conversation(entry["text"])
        if match is None:
            return
        addressee = self.boundaries.addressee()
        if addressee and addressee.pane == match.session.pane:
            return
        purpose = self.boundaries.listening_purpose()
        if not self.dry_run:
            self.boundaries.hand_to(
                Addressee(match.session.pane, match.session.servant, entry["sequence"])
            )
        self.deliver(match, purpose)

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
