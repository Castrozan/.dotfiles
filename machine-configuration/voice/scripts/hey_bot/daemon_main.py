from __future__ import annotations

import signal

from assistant_gateway import AssistantGateway
from audio_capture import AudioCapture
from background_commands import BackgroundCommandRunner
from console_output import ConsoleOutput
from conversation_state import MachineSettings
from daemon_actions import DaemonActions
from daemon_runtime import HeyBotDaemon
from desktop_notifier import DesktopNotifier
from gateway_reply_speech import (
    UNPARSABLE_REPLY_SPEECH,
    UNREACHABLE_GATEWAY_SPEECH,
    FailureSpeech,
)
from runtime_environment import (
    gateway_settings,
    keywords_pattern,
    maximum_log_size_bytes,
    speech_voice,
    transcription_directory,
    whisper_model,
)
from signal_files import SignalFiles, default_signal_file_paths
from speech_synthesizer import SpeechSynthesizer
from speech_transcriber import SpeechTranscriber
from system_clock import SystemClock
from transcription_log import TranscriptionLog
from voice_command_dispatch import VoiceCommandDispatcher


def build_daemon() -> HeyBotDaemon:
    clock = SystemClock()
    console = ConsoleOutput()
    transcription_log = TranscriptionLog(
        transcription_directory(), maximum_log_size_bytes(), clock.formatted_now
    )
    transcription_log.prepare_directory()
    signal_files = SignalFiles(default_signal_file_paths())
    actions = DaemonActions(
        console=console,
        notifier=DesktopNotifier(),
        transcription_log=transcription_log,
        signal_files=signal_files,
        synthesizer=SpeechSynthesizer(speech_voice()),
        dispatch_command=lambda command_text: background_commands.start(command_text),
    )
    dispatcher = VoiceCommandDispatcher(
        gateway=AssistantGateway(gateway_settings()),
        transcription_log=transcription_log,
        perform_actions=actions.perform_all,
        console=console,
        failure_speech=FailureSpeech(
            unreachable=UNREACHABLE_GATEWAY_SPEECH,
            unparsable=UNPARSABLE_REPLY_SPEECH,
        ),
    )
    background_commands = BackgroundCommandRunner(
        run_command=dispatcher.run, report_failure=console.write_line
    )
    return HeyBotDaemon(
        settings=MachineSettings(keywords_pattern()),
        capture=AudioCapture(),
        transcriber=SpeechTranscriber(whisper_model()),
        signal_files=signal_files,
        actions=actions,
        background_commands=background_commands,
        clock=clock,
        console=console,
    )


def main() -> None:
    daemon = build_daemon()
    for stop_signal in (signal.SIGTERM, signal.SIGINT):
        signal.signal(stop_signal, lambda _number, _frame: daemon.request_stop())
    daemon.run()


if __name__ == "__main__":
    main()
