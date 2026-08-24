from __future__ import annotations

from collections.abc import Callable

from hey_bot.process_execution import CommandResult, run_command


class PushToTalkCapture:
    def __init__(self, run_process: Callable[..., CommandResult] = run_command):
        self._run_process = run_process

    def stop_recorder(self) -> None:
        self._run_process(["whisp-away", "stop", "--clipboard", "true"])

    def read_clipboard(self) -> str:
        result = self._run_process(["wl-paste"])
        if not result.succeeded:
            return ""
        return result.output.strip()
