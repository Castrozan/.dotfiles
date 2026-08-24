from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from hey_bot.process_execution import CommandResult, RunningCommand, run_command, start_command
from hey_bot.temporary_paths import create_temporary_file

CHUNK_DURATION_SECONDS = 6
STEP_INTERVAL_SECONDS = 4
ENERGY_THRESHOLD = 0.02
CHUNK_FILE_PREFIX = "hey-bot-"
CHUNK_FILE_SUFFIX = ".wav"
MAXIMUM_AMPLITUDE_LABEL = "Maximum amplitude:"


def parse_maximum_amplitude(statistics_output: str) -> float | None:
    for line in statistics_output.splitlines():
        if MAXIMUM_AMPLITUDE_LABEL not in line:
            continue
        try:
            return float(line.split()[-1])
        except ValueError:
            return None
    return None


class AudioCapture:
    def __init__(
        self,
        run_process: Callable[..., CommandResult] = run_command,
        start_process: Callable[..., RunningCommand] = start_command,
        create_chunk_path: Callable[[str, str], Path] = create_temporary_file,
    ):
        self._run_process = run_process
        self._start_process = start_process
        self._create_chunk_path = create_chunk_path

    def create_chunk_file(self) -> Path:
        return self._create_chunk_path(CHUNK_FILE_PREFIX, CHUNK_FILE_SUFFIX)

    def start_chunk_recording(self, chunk_path: Path) -> RunningCommand:
        return self._start_process(
            [
                "rec",
                "-q",
                str(chunk_path),
                "rate",
                "16k",
                "channels",
                "1",
                "trim",
                "0",
                str(CHUNK_DURATION_SECONDS),
            ]
        )

    def chunk_has_audio(self, chunk_path: Path) -> bool:
        statistics = self._run_process(
            ["sox", str(chunk_path), "-n", "stat"], merge_error_output=True
        )
        maximum_amplitude = parse_maximum_amplitude(statistics.output)
        return maximum_amplitude is not None and maximum_amplitude >= ENERGY_THRESHOLD
