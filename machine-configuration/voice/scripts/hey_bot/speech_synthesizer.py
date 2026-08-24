from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from process_execution import CommandResult, run_command
from temporary_paths import create_temporary_file

SPEECH_FILE_PREFIX = "hey-bot-tts-"
SPEECH_FILE_SUFFIX = ".mp3"
DEFAULT_AUDIO_SINK = "@DEFAULT_AUDIO_SINK@"


class SpeechSynthesizer:
    def __init__(
        self,
        voice: str,
        run_process: Callable[..., CommandResult] = run_command,
        create_speech_path: Callable[[str, str], Path] = create_temporary_file,
    ):
        self._voice = voice
        self._run_process = run_process
        self._create_speech_path = create_speech_path

    def speak(self, text: str) -> None:
        speech_path = self._create_speech_path(SPEECH_FILE_PREFIX, SPEECH_FILE_SUFFIX)
        try:
            rendered = self._run_process(
                [
                    "edge-tts",
                    "--text",
                    text,
                    "--voice",
                    self._voice,
                    "--write-media",
                    str(speech_path),
                ]
            )
            if not rendered.succeeded:
                return
            self._run_process(["wpctl", "set-mute", DEFAULT_AUDIO_SINK, "0"])
            self._run_process(["mpv", "--no-video", "--ao=pulse", str(speech_path)])
        finally:
            speech_path.unlink(missing_ok=True)
