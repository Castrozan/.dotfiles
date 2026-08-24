from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

CURRENT_LOG_FILE_NAME = "current.log"
LOG_FILE_GLOB = "*.log"
ROTATED_NAME_TIMESTAMP_PATTERN = "%Y-%m-%d_%H-%M-%S"
LINE_TIMESTAMP_PATTERN = "%Y-%m-%d %H:%M:%S"
RECENT_LINE_COUNT = 20


def latest_log_file(directory: Path) -> Path | None:
    log_files = [
        candidate for candidate in directory.glob(LOG_FILE_GLOB) if candidate.is_file()
    ]
    if not log_files:
        return None
    return max(log_files, key=lambda candidate: candidate.stat().st_mtime)


class TranscriptionLog:
    def __init__(
        self,
        directory: Path,
        maximum_size_bytes: int,
        formatted_now: Callable[[str], str],
    ):
        self._directory = directory
        self._maximum_size_bytes = maximum_size_bytes
        self._formatted_now = formatted_now

    def prepare_directory(self) -> None:
        self._directory.mkdir(parents=True, exist_ok=True)

    def current_file(self) -> Path:
        current_path = self._directory / CURRENT_LOG_FILE_NAME
        if (
            current_path.is_file()
            and current_path.stat().st_size > self._maximum_size_bytes
        ):
            rotated_name = self._formatted_now(ROTATED_NAME_TIMESTAMP_PATTERN)
            current_path.rename(self._directory / f"{rotated_name}.log")
        return current_path

    def append(self, text: str) -> None:
        timestamp = self._formatted_now(LINE_TIMESTAMP_PATTERN)
        with self.current_file().open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{timestamp}] {text}\n")

    def recent_lines(self) -> str:
        current_path = self.current_file()
        if not current_path.is_file():
            return ""
        lines = current_path.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[-RECENT_LINE_COUNT:])
