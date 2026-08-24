from __future__ import annotations

from collections.abc import Callable

from hey_bot.process_execution import CommandResult, run_command

NOTIFICATION_TITLE = "Hey Bot"


class DesktopNotifier:
    def __init__(self, run_process: Callable[..., CommandResult] = run_command):
        self._run_process = run_process

    def notify(self, body: str) -> None:
        self._run_process(["notify-send", NOTIFICATION_TITLE, body])
