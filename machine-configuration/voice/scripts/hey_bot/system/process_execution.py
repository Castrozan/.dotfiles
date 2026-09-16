from __future__ import annotations

import subprocess
from collections.abc import Sequence
from dataclasses import dataclass

MISSING_PROGRAM_EXIT_CODE = 127


@dataclass(frozen=True)
class CommandResult:
    exit_code: int
    output: str

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0


class RunningCommand:
    def __init__(self, process: subprocess.Popen[bytes]):
        self._process = process

    def wait(self) -> None:
        self._process.wait()

    def terminate(self) -> None:
        if self._process.poll() is None:
            self._process.terminate()
        self._process.wait()


def run_command(
    arguments: Sequence[str], merge_error_output: bool = False
) -> CommandResult:
    error_destination = subprocess.STDOUT if merge_error_output else subprocess.DEVNULL
    try:
        completed_process = subprocess.run(
            list(arguments),
            stdout=subprocess.PIPE,
            stderr=error_destination,
            check=False,
        )
    except OSError:
        return CommandResult(MISSING_PROGRAM_EXIT_CODE, "")
    output = completed_process.stdout.decode("utf-8", errors="replace")
    return CommandResult(completed_process.returncode, output)


def start_command(arguments: Sequence[str]) -> RunningCommand:
    return RunningCommand(
        subprocess.Popen(
            list(arguments),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    )
