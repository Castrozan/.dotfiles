from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hey_bot.temporary_paths import temporary_directory

FOLLOWUP_FLAG_FILE_NAME = "hey-bot-followup"
WAIT_CONTEXT_FILE_NAME = "hey-bot-wait-context"
KEYWORDS_DISABLED_FLAG_PATH = Path("/tmp/hey-bot-keywords-disabled")


@dataclass(frozen=True)
class SignalFilePaths:
    followup_flag: Path
    wait_context: Path
    keywords_disabled: Path


def default_signal_file_paths() -> SignalFilePaths:
    directory = temporary_directory()
    return SignalFilePaths(
        followup_flag=directory / FOLLOWUP_FLAG_FILE_NAME,
        wait_context=directory / WAIT_CONTEXT_FILE_NAME,
        keywords_disabled=KEYWORDS_DISABLED_FLAG_PATH,
    )


class SignalFiles:
    def __init__(self, paths: SignalFilePaths):
        self._paths = paths

    def keywords_disabled(self) -> bool:
        return self._paths.keywords_disabled.exists()

    def raise_followup_signal(self) -> None:
        self._paths.followup_flag.touch()

    def consume_followup_signal(self) -> bool:
        if not self._paths.followup_flag.exists():
            return False
        self._paths.followup_flag.unlink(missing_ok=True)
        return True

    def read_wait_context(self) -> str:
        if not self._paths.wait_context.is_file():
            return ""
        return self._paths.wait_context.read_text(encoding="utf-8").strip()

    def save_wait_context(self, command_text: str) -> None:
        self._paths.wait_context.write_text(f"{command_text}\n", encoding="utf-8")

    def clear_wait_context(self) -> None:
        self._paths.wait_context.unlink(missing_ok=True)

    def discard_stale_signals(self) -> None:
        self._paths.followup_flag.unlink(missing_ok=True)
        self._paths.wait_context.unlink(missing_ok=True)
