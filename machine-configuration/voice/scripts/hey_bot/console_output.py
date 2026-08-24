from __future__ import annotations

import sys


class ConsoleOutput:
    def write_line(self, message: str) -> None:
        print(message, flush=True)

    def write_text(self, text: str) -> None:
        sys.stdout.write(text)
        sys.stdout.flush()

    def write_error_line(self, message: str) -> None:
        print(message, file=sys.stderr, flush=True)
