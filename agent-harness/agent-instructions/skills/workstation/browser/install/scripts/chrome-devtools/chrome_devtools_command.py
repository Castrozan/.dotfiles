from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from chrome_devtools_session import ChromeDevtoolsSession
from chrome_devtools_connect import connect


@dataclass(frozen=True)
class ChromeDevtoolsConfiguration:
    upstream_executable: str
    home_directory: Path
    ffmpeg_executable: str
    chrome_executable: str
    consent_helper: tuple[str, ...] = ()

    @classmethod
    def read(cls, path):
        configuration = json.loads(path.read_text())
        return cls(
            configuration["upstreamExecutable"],
            Path(configuration["homeDirectory"]),
            configuration["ffmpegExecutable"],
            configuration["chromeExecutable"],
            tuple(configuration.get("consentHelper", ())),
        )

    def start_arguments(self, mode):
        arguments = [
            "--usageStatistics",
            "false",
            "--experimentalScreencast",
            "--experimentalFfmpegPath",
            self.ffmpeg_executable,
        ]
        if mode == "headless":
            return arguments + [
                "--headless",
                "--userDataDir",
                str(self.home_directory / ".config/chrome-devtools-headless"),
                "--executablePath",
                self.chrome_executable,
            ]
        return arguments + [
            "--autoConnect",
            "--headless=false",
            "--userDataDir",
            str(self.home_directory / ".config/chrome-global"),
        ]


def following_argument(arguments, index):
    return arguments[index + 1] if index + 1 < len(arguments) else "true"


def headless_requested(arguments):
    enabled = False
    for index, argument in enumerate(arguments):
        if argument.startswith("--headless="):
            enabled = argument.partition("=")[2].lower() == "true"
        elif argument == "--headless":
            value = following_argument(arguments, index)
            enabled = value.lower() != "false"
        elif argument == "--no-headless":
            enabled = False
    return enabled


def upstream_command(configuration, session, arguments):
    return [
        configuration.upstream_executable,
        "--sessionId",
        session.identifier,
        *arguments,
    ]


def start_worker(configuration, session, mode, arguments=(), timeout=35):
    session.record_mode(mode, configuration.upstream_executable)
    command = upstream_command(
        configuration,
        session,
        ["start", *configuration.start_arguments(mode), *arguments],
    )
    return subprocess.run(command, check=False, timeout=timeout).returncode


def stop_worker(configuration, session, timeout=15):
    command = upstream_command(configuration, session, ["stop"])
    result = subprocess.run(command, check=False, timeout=timeout)
    if result.returncode:
        return result.returncode
    deadline = time.monotonic() + 5
    while session.running():
        if time.monotonic() >= deadline:
            raise RuntimeError("Chrome DevTools worker did not stop")
        time.sleep(0.05)
    session.clear()
    return 0


def validate_session_arguments(arguments):
    if any(argument.startswith("--sessionId") for argument in arguments):
        raise ValueError("Chrome DevTools session ownership is managed automatically")


def unused_cleanup(session, operation):
    return operation == "cleanup" and (
        not session.automatic_cleanup or not session.state_file.exists()
    )


def attached_idle_allowance(arguments):
    option = "--keep-attached-for"
    if option not in arguments:
        return None
    index = arguments.index(option)
    try:
        return float(arguments[index + 1])
    except (IndexError, ValueError):
        raise ValueError(f"{option} needs a number of seconds") from None


def keeps_attached_worker(session, arguments):
    allowance = attached_idle_allowance(arguments)
    return (
        allowance is not None
        and session.mode() == "attached"
        and session.idle_seconds() < allowance
    )


def inspection_requested(arguments, operation):
    return (
        not arguments or "--help" in arguments or operation in ("--version", "status")
    )


def inspect_worker(configuration, session, arguments, operation):
    if not arguments or arguments == ["--help"] or operation == "start":
        print(
            "Managed Chrome DevTools CLI: connect attaches to Chrome Global; "
            "connect verifies pages within 20 seconds; connect --help describes native consent. "
            "start --headless uses a separate profile. Workers start on demand. "
            "stop closes this worker; cleanup closes an agent-owned worker. "
            "The agent completion hook runs cleanup --keep-attached-for SECONDS for Herdr panes and Codex threads: "
            "it keeps an attached worker that was used within that time, so Chrome's consent survives between turns, "
            "and closes every other worker.\n",
            flush=True,
        )
    command = upstream_command(configuration, session, arguments or ["--help"])
    return os.execv(configuration.upstream_executable, command)


def start_requested_worker(configuration, session, arguments):
    mode = "headless" if headless_requested(arguments[1:]) else "attached"
    if mode == "attached":
        raise RuntimeError("Run connect to start an attached worker")
    return start_worker(configuration, session, mode, arguments[1:])


def invoke_browser(configuration, session, arguments, operation):
    with session.locked():
        if operation == "start":
            return start_requested_worker(configuration, session, arguments)
        if not session.running():
            if session.mode() == "attached":
                raise RuntimeError(
                    "Run connect before requesting attached browser tools"
                )
            result = start_worker(configuration, session, session.mode())
            if result:
                return result
        session.require_current_worker(configuration.upstream_executable)
        session.touch()
    command = upstream_command(configuration, session, arguments)
    return os.execv(configuration.upstream_executable, command)


def run_worker_operation(configuration, session, arguments, operation):
    if operation in ("stop", "cleanup"):
        with session.locked():
            if operation == "cleanup" and keeps_attached_worker(session, arguments[1:]):
                return 0
            return stop_worker(configuration, session)
    if inspection_requested(arguments, operation):
        return inspect_worker(configuration, session, arguments, operation)
    attached = not (operation == "start" and headless_requested(arguments[1:]))
    with session.attached_locked(required=attached):
        return invoke_browser(configuration, session, arguments, operation)


def main(configuration, arguments):
    session = ChromeDevtoolsSession.current(configuration.home_directory)
    operation = arguments[0] if arguments else "--help"
    validate_session_arguments(arguments)
    if operation == "connect":
        return connect(configuration, session, arguments[1:], start_worker, stop_worker)
    if unused_cleanup(session, operation):
        return 0
    return run_worker_operation(configuration, session, arguments, operation)


if __name__ == "__main__":
    try:
        sys.exit(
            main(ChromeDevtoolsConfiguration.read(Path(sys.argv[1])), sys.argv[2:])
        )
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"chrome-devtools: {error}", file=sys.stderr)
        sys.exit(1)
