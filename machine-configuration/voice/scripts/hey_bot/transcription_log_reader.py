from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from console_output import ConsoleOutput
from transcription_log import latest_log_file

MISSING_LOGS_EXIT_CODE = 1


def follow_log(log_file: Path) -> None:
    os.execvp("tail", ["tail", "-f", str(log_file)])


class TranscriptionLogReader:
    def __init__(
        self,
        directory: Path,
        console: ConsoleOutput,
        follow_log_file: Callable[[Path], None] = follow_log,
    ):
        self._directory = directory
        self._console = console
        self._follow_log_file = follow_log_file

    def run(self, follow: bool) -> int:
        log_file = latest_log_file(self._directory)
        if log_file is None:
            self._console.write_line(
                f"No transcription logs found in {self._directory}"
            )
            return MISSING_LOGS_EXIT_CODE
        if follow:
            self._follow_log_file(log_file)
            return 0
        self._console.write_text(log_file.read_text(encoding="utf-8", errors="replace"))
        return 0
