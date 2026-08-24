from __future__ import annotations

from collections.abc import Callable, Iterable

from hey_bot.console_output import ConsoleOutput
from hey_bot.conversation_actions import (
    AnnounceAction,
    ClearWaitContextAction,
    ConversationAction,
    DispatchCommandAction,
    LogTranscriptionAction,
    NotifyAction,
    RaiseFollowupSignalAction,
    SaveWaitContextAction,
    SpeakAction,
)
from hey_bot.desktop_notifier import DesktopNotifier
from hey_bot.signal_files import SignalFiles
from hey_bot.speech_synthesizer import SpeechSynthesizer
from hey_bot.transcription_log import TranscriptionLog


class DaemonActions:
    def __init__(
        self,
        console: ConsoleOutput,
        notifier: DesktopNotifier,
        transcription_log: TranscriptionLog,
        signal_files: SignalFiles,
        synthesizer: SpeechSynthesizer,
        dispatch_command: Callable[[str], None],
    ):
        self._console = console
        self._notifier = notifier
        self._transcription_log = transcription_log
        self._signal_files = signal_files
        self._synthesizer = synthesizer
        self._dispatch_command = dispatch_command

    def perform_all(self, actions: Iterable[ConversationAction]) -> None:
        for action in actions:
            self.perform(action)

    def perform(self, action: ConversationAction) -> None:
        match action:
            case AnnounceAction(message):
                self._console.write_line(message)
            case LogTranscriptionAction(text):
                self._transcription_log.append(text)
            case NotifyAction(body):
                self._notifier.notify(body)
            case DispatchCommandAction(command_text):
                self._dispatch_command(command_text)
            case SpeakAction(text):
                self._synthesizer.speak(text)
            case SaveWaitContextAction(command_text):
                self._signal_files.save_wait_context(command_text)
            case ClearWaitContextAction():
                self._signal_files.clear_wait_context()
            case RaiseFollowupSignalAction():
                self._signal_files.raise_followup_signal()
