from dataclasses import dataclass

from hey_bot.conversation_state import MachineSettings
from hey_bot.daemon_runtime import HeyBotDaemon
from hey_bot_boundary_fakes import RecordingConsole
from hey_bot.signal_files import SignalFilePaths, SignalFiles


class FakeRecording:
    def __init__(self):
        self.waited = False
        self.terminated = False

    def wait(self):
        self.waited = True

    def terminate(self):
        self.terminated = True


class FakeCapture:
    def __init__(self, chunk_directory, chunk_has_audio=True):
        self._chunk_directory = chunk_directory
        self._chunk_has_audio = chunk_has_audio
        self.created_chunks = []
        self.recordings = []

    def create_chunk_file(self):
        chunk_path = self._chunk_directory / f"chunk-{len(self.created_chunks)}.wav"
        chunk_path.write_bytes(b"")
        self.created_chunks.append(chunk_path)
        return chunk_path

    def start_chunk_recording(self, _chunk_path):
        recording = FakeRecording()
        self.recordings.append(recording)
        return recording

    def chunk_has_audio(self, _chunk_path):
        return self._chunk_has_audio


class ScriptedTranscriber:
    def __init__(self, transcriptions=()):
        self._transcriptions = list(transcriptions)
        self.transcribed_chunks = []

    def transcribe(self, chunk_path):
        self.transcribed_chunks.append(chunk_path)
        if not self._transcriptions:
            return ""
        return self._transcriptions.pop(0)


class StoppingClock:
    def __init__(self, stop_after_sleeps):
        self._stop_after_sleeps = stop_after_sleeps
        self.daemon = None
        self.slept_seconds = []

    def monotonic_seconds(self):
        return 0.0

    def sleep(self, seconds):
        self.slept_seconds.append(seconds)
        if len(self.slept_seconds) >= self._stop_after_sleeps:
            self.daemon.request_stop()


class RecordingBackgroundCommands:
    def __init__(self):
        self.started = []
        self.waited_for_completion = False

    def start(self, command_text):
        self.started.append(command_text)

    def wait_for_completion(self):
        self.waited_for_completion = True


class CollectingActions:
    def __init__(self):
        self.performed = []

    def perform_all(self, actions):
        self.performed.extend(actions)


def signal_file_paths(directory):
    return SignalFilePaths(
        followup_flag=directory / "hey-bot-followup",
        wait_context=directory / "hey-bot-wait-context",
        keywords_disabled=directory / "hey-bot-keywords-disabled",
    )


@dataclass
class DaemonHarness:
    daemon: HeyBotDaemon
    capture: FakeCapture
    transcriber: ScriptedTranscriber
    actions: CollectingActions
    background_commands: RecordingBackgroundCommands
    signal_files: SignalFiles
    console: RecordingConsole


def build_daemon(
    tmp_path,
    transcriptions=(),
    stop_after_sleeps=1,
    chunk_has_audio=True,
    signal_files=None,
):
    chunk_directory = tmp_path / "chunks"
    chunk_directory.mkdir(exist_ok=True)
    clock = StoppingClock(stop_after_sleeps)
    harness = DaemonHarness(
        daemon=None,
        capture=FakeCapture(chunk_directory, chunk_has_audio),
        transcriber=ScriptedTranscriber(transcriptions),
        actions=CollectingActions(),
        background_commands=RecordingBackgroundCommands(),
        signal_files=signal_files or SignalFiles(signal_file_paths(tmp_path)),
        console=RecordingConsole(),
    )
    harness.daemon = HeyBotDaemon(
        settings=MachineSettings(keywords_pattern="clever|jarvis"),
        capture=harness.capture,
        transcriber=harness.transcriber,
        signal_files=harness.signal_files,
        actions=harness.actions,
        background_commands=harness.background_commands,
        clock=clock,
        console=harness.console,
    )
    clock.daemon = harness.daemon
    return harness
