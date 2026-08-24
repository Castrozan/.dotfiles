from dataclasses import dataclass, field

import pytest
from hey_bot.conversation_actions import (
    AnnounceAction,
    ClearWaitContextAction,
    DispatchCommandAction,
    LogTranscriptionAction,
    NotifyAction,
    RaiseFollowupSignalAction,
    SaveWaitContextAction,
    SpeakAction,
)
from hey_bot.daemon_actions import DaemonActions
from hey_bot_boundary_fakes import (
    FakeTranscriptionLog,
    RecordingConsole,
    RecordingNotifier,
    RecordingSynthesizer,
)
from hey_bot_daemon_fakes import signal_file_paths
from hey_bot.signal_files import SignalFilePaths, SignalFiles


@dataclass
class ActionHarness:
    paths: SignalFilePaths
    console: RecordingConsole = field(default_factory=RecordingConsole)
    notifier: RecordingNotifier = field(default_factory=RecordingNotifier)
    transcription_log: FakeTranscriptionLog = field(
        default_factory=FakeTranscriptionLog
    )
    synthesizer: RecordingSynthesizer = field(default_factory=RecordingSynthesizer)
    dispatched: list = field(default_factory=list)

    def actions(self):
        return DaemonActions(
            console=self.console,
            notifier=self.notifier,
            transcription_log=self.transcription_log,
            signal_files=SignalFiles(self.paths),
            synthesizer=self.synthesizer,
            dispatch_command=self.dispatched.append,
        )


@pytest.fixture
def harness(tmp_path):
    return ActionHarness(signal_file_paths(tmp_path))


def test_every_action_reaches_the_boundary_that_owns_it(harness):
    harness.actions().perform_all(
        [
            AnnounceAction("hey-bot: listening"),
            LogTranscriptionAction("the coffee machine is running"),
            NotifyAction("Listening..."),
            DispatchCommandAction("hey clever what is the weather"),
            SpeakAction("The weather is fine."),
        ]
    )

    assert harness.console.lines == ["hey-bot: listening"]
    assert harness.transcription_log.appended == ["the coffee machine is running"]
    assert harness.notifier.bodies == ["Listening..."]
    assert harness.dispatched == ["hey clever what is the weather"]
    assert harness.synthesizer.spoken == ["The weather is fine."]


def test_the_wait_context_is_saved_raised_and_cleared_through_the_signal_files(harness):
    actions = harness.actions()

    actions.perform(SaveWaitContextAction("hey clever turn on the"))
    actions.perform(RaiseFollowupSignalAction())

    assert harness.paths.wait_context.read_text(encoding="utf-8").strip() == (
        "hey clever turn on the"
    )
    assert harness.paths.followup_flag.exists()

    actions.perform(ClearWaitContextAction())

    assert not harness.paths.wait_context.exists()
