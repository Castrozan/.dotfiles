from __future__ import annotations

from pathlib import Path

from audio_capture import STEP_INTERVAL_SECONDS, AudioCapture
from background_commands import BackgroundCommandRunner
from console_output import ConsoleOutput
from conversation_machine import advance
from conversation_state import ChunkObservation, ConversationState, MachineSettings
from daemon_actions import DaemonActions
from signal_files import SignalFiles
from speech_transcriber import SpeechTranscriber
from system_clock import SystemClock


class HeyBotDaemon:
    def __init__(
        self,
        settings: MachineSettings,
        capture: AudioCapture,
        transcriber: SpeechTranscriber,
        signal_files: SignalFiles,
        actions: DaemonActions,
        background_commands: BackgroundCommandRunner,
        clock: SystemClock,
        console: ConsoleOutput,
    ):
        self._settings = settings
        self._capture = capture
        self._transcriber = transcriber
        self._signal_files = signal_files
        self._actions = actions
        self._background_commands = background_commands
        self._clock = clock
        self._console = console
        self._state = ConversationState()
        self._stop_requested = False

    def request_stop(self) -> None:
        self._stop_requested = True

    def run(self) -> None:
        self._signal_files.discard_stale_signals()
        self._console.write_line(
            "hey-bot: listening for keywords matching: "
            f"{self._settings.keywords_pattern}"
        )
        try:
            self.run_recording_loop()
        finally:
            self.shut_down()

    def run_recording_loop(self) -> None:
        previous_recording = None
        previous_chunk_path = None
        while not self._stop_requested:
            chunk_path = self._capture.create_chunk_file()
            recording = self._capture.start_chunk_recording(chunk_path)
            iteration_start = self._clock.monotonic_seconds()
            if previous_recording is not None:
                previous_recording.wait()
            if previous_chunk_path is not None:
                self.process_chunk(previous_chunk_path)
            previous_recording = recording
            previous_chunk_path = chunk_path
            self._sleep_remaining_step(iteration_start)
        if previous_recording is not None:
            previous_recording.terminate()
        if previous_chunk_path is not None:
            previous_chunk_path.unlink(missing_ok=True)

    def process_chunk(self, chunk_path: Path) -> None:
        transcription = ""
        if self._capture.chunk_has_audio(chunk_path):
            transcription = self._transcriber.transcribe(chunk_path)
        chunk_path.unlink(missing_ok=True)
        observation = ChunkObservation(
            transcription=transcription,
            followup_signalled=self._signal_files.consume_followup_signal(),
            keywords_disabled=self._signal_files.keywords_disabled(),
            wait_context=self._signal_files.read_wait_context(),
        )
        transition = advance(self._state, observation, self._settings)
        self._state = transition.state
        self._actions.perform_all(transition.actions)

    def shut_down(self) -> None:
        self._background_commands.wait_for_completion()
        self._signal_files.discard_stale_signals()

    def _sleep_remaining_step(self, iteration_start: float) -> None:
        elapsed = self._clock.monotonic_seconds() - iteration_start
        remaining_seconds = STEP_INTERVAL_SECONDS - elapsed
        if remaining_seconds > 0:
            self._clock.sleep(remaining_seconds)
