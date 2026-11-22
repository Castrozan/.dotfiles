import argparse
import subprocess
import time

import peer_sessions
import room_holder
import speech_segmenter
import transcript_log
import wake_claim
import wake_prompts
from quiet_conversation import (
    ARM_CHECK_SECONDS,
    ConversationTranscript,
    follow_conversation,
)
from voice_addressing import VoiceAddressing
from wake_boundaries import for_this_machine, microphone_frames

FLEET_REFRESH_SECONDS = 60
TRANSCRIBER_ATTEMPTS = 5
TRANSCRIBER_RETRY_SECONDS = 0.4
TRANSCRIBER_UNAVAILABLE = (OSError, subprocess.SubprocessError)
FRAMES_PER_ARM_CHECK = int(ARM_CHECK_SECONDS / speech_segmenter.FRAME_SECONDS)
MEETING_SOURCE = "meeting"


class WakeListener:
    def __init__(self, boundaries, dry_run):
        self.boundaries = boundaries
        self.dry_run = dry_run
        self.sessions = []
        self.sessions_read_at = None
        self.conversation = ConversationTranscript()
        self.addressing = VoiceAddressing(
            boundaries, self.known_sessions, self.refresh_sessions
        )

    def refresh_sessions(self):
        self.sessions = self.boundaries.sessions()
        self.sessions_read_at = self.boundaries.now()
        return self.sessions

    def sessions_stale(self):
        return (
            self.sessions_read_at is None
            or self.boundaries.now() - self.sessions_read_at >= FLEET_REFRESH_SECONDS
        )

    def known_sessions(self):
        if self.sessions_stale():
            self.refresh_sessions()
        return self.sessions

    def armed(self):
        return (
            bool(self.known_sessions()) and not self.boundaries.conversation_listening()
        )

    def transcribed(self, segment):
        for _ in range(TRANSCRIBER_ATTEMPTS - 1):
            try:
                return self.boundaries.transcribe(segment)
            except TRANSCRIBER_UNAVAILABLE:
                self.boundaries.pause(TRANSCRIBER_RETRY_SECONDS)
        return self.boundaries.transcribe(segment)

    def hear(self, segment):
        try:
            self.answer(segment)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            self.boundaries.report(f"Dropped an utterance: {error}")

    def holds_the_room(self, session):
        discord_host = self.boundaries.discord_call_host()
        if discord_host:
            self.boundaries.report(
                f"left {session.servant} to the Discord call on {discord_host}"
            )
            return False
        if self.dry_run or self.boundaries.claim_wake(session):
            return True
        self.boundaries.report(f"left {session.servant} to another room")
        return False

    def answer(self, segment):
        heard = self.transcribed(segment)
        transcript_log.report_wake(self.boundaries.report, heard, segment)
        if not heard:
            self.boundaries.report("Ignored wake: empty transcript")
            return
        match = self.addressing.wake_match(heard)
        if match is None or not self.holds_the_room(match.session):
            return
        if not wake_prompts.deliver(self.boundaries, self.dry_run, match, purpose=None):
            return
        self.boundaries.open_conversation()
        self.boundaries.hand_to(room_holder.addressee_of(match.session, 0))

    def start_reading_conversation(self):
        self.conversation.start(self.boundaries.transcript_entries())
        self.addressing.forget_turns()

    def read_conversation(self):
        try:
            self.turn_on_new_entries()
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            self.boundaries.report(f"Dropped a conversation turn: {error}")

    def turn_on_new_entries(self):
        for entry in self.conversation.new_entries(
            self.boundaries.transcript_entries()
        ):
            self.turn_to(entry)
        self.decide_whom_it_addresses(
            self.conversation.turn_ended_in_quiet(
                self.boundaries.now(), self.boundaries.speech_in_progress
            )
        )

    def turn_to(self, entry):
        transcript_log.report_conversation(self.boundaries.report, entry)
        self.decide_whom_it_addresses(
            self.conversation.completed_turn(entry, self.boundaries.now())
        )

    def decide_whom_it_addresses(self, turn):
        if turn is None:
            return
        match = self.addressing.conversation_match(turn)
        if match is None:
            return
        if not self.dry_run:
            self.boundaries.hand_to(
                room_holder.addressee_of(match.session, turn["sequence"])
            )
        self.deliver_to_the_listening_purpose(match, turn)

    def deliver_to_the_listening_purpose(self, match, entry):
        purpose = self.boundaries.listening_purpose()
        if entry.get("source") != MEETING_SOURCE and purpose in wake_prompts.SETTINGS:
            wake_prompts.deliver(
                self.boundaries, self.dry_run, match, purpose, entry["sequence"]
            )

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


def run(wake):
    while True:
        if wake.boundaries.conversation_listening():
            follow_conversation(wake)
            continue
        if not wake.armed():
            time.sleep(ARM_CHECK_SECONDS)
            continue
        capture = subprocess.Popen(
            wake.boundaries.capture_command(), stdout=subprocess.PIPE
        )
        try:
            while wake.listen_while_armed(microphone_frames(capture)):
                pass
        finally:
            capture.terminate()
            capture.wait()


def main():
    parser = argparse.ArgumentParser(prog="avatar-wake")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sessions", action="store_true")
    parser.add_argument("--conversation", action="store_true")
    parser.add_argument("--claim")
    parser.add_argument("--room")
    arguments = parser.parse_args()
    if arguments.conversation:
        print(wake_claim.conversation_report())
        return
    if arguments.claim:
        raise SystemExit(wake_claim.exit_status(arguments.claim, arguments.room))
    if arguments.sessions:
        print(peer_sessions.this_machine_listing())
        return
    run(WakeListener(for_this_machine(), arguments.dry_run))


if __name__ == "__main__":
    main()
