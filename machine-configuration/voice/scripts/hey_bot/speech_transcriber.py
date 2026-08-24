from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from process_execution import CommandResult, run_command
from transcription_text import clean_transcription, is_non_latin_hallucination

WHISPER_ARGUMENTS = ["-nt", "-np", "-l", "auto", "--suppress-nst"]


class SpeechTranscriber:
    def __init__(
        self,
        whisper_model: str,
        run_process: Callable[..., CommandResult] = run_command,
    ):
        self._whisper_model = whisper_model
        self._run_process = run_process

    def transcribe(self, chunk_path: Path) -> str:
        result = self._run_process(
            [
                "whisper-cli",
                "-m",
                self._whisper_model,
                "-f",
                str(chunk_path),
                *WHISPER_ARGUMENTS,
            ]
        )
        transcription = clean_transcription(result.output)
        if is_non_latin_hallucination(transcription):
            return ""
        return transcription
