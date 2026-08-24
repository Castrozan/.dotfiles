from __future__ import annotations

import threading
from collections.abc import Callable

BACKGROUND_FAILURE_MESSAGE = "hey-bot: background command failed"


class BackgroundCommandRunner:
    def __init__(
        self,
        run_command: Callable[[str], None],
        report_failure: Callable[[str], None],
    ):
        self._run_command = run_command
        self._report_failure = report_failure
        self._running_threads: list[threading.Thread] = []

    @property
    def pending_command_count(self) -> int:
        return len(self._running_threads)

    def start(self, command_text: str) -> None:
        self._forget_finished_threads()
        thread = threading.Thread(target=self._run_guarded, args=(command_text,))
        self._running_threads.append(thread)
        thread.start()

    def wait_for_completion(self) -> None:
        for thread in list(self._running_threads):
            thread.join()
        self._forget_finished_threads()

    def _run_guarded(self, command_text: str) -> None:
        try:
            self._run_command(command_text)
        except Exception as failure:
            self._report_failure(f"{BACKGROUND_FAILURE_MESSAGE}: {failure}")

    def _forget_finished_threads(self) -> None:
        self._running_threads = [
            thread for thread in self._running_threads if thread.is_alive()
        ]
