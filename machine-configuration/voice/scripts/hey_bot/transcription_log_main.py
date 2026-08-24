from __future__ import annotations

import sys

from hey_bot.console_output import ConsoleOutput
from hey_bot.runtime_environment import transcription_directory
from hey_bot.transcription_log_reader import TranscriptionLogReader

FOLLOW_FLAG = "-f"


def main(arguments: list[str]) -> int:
    reader = TranscriptionLogReader(transcription_directory(), ConsoleOutput())
    return reader.run(follow=bool(arguments) and arguments[0] == FOLLOW_FLAG)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
