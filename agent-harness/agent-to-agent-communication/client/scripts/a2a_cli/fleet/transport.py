"""Deadline and output bounded local/SSH command execution."""

import os
import selectors
import shlex
import signal
import subprocess
import time

MAX_OUTPUT_BYTES = 2 * 1024 * 1024
EMPTY_DIRECTORY = b"the a2a daemon is running but no pane is hosting an agent right now"


class ObservationError(Exception):
    def __init__(self, kind):
        self.kind = kind
        super().__init__(kind)


def command_argv(host, command):
    if host["transport"] == "local":
        return command
    return [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=5",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        "ClearAllForwardings=yes",
        "--",
        host["transport"],
        shlex.join(command),
    ]


def start(host, command):
    try:
        return subprocess.Popen(
            command_argv(host, command),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
    except OSError as error:
        raise ObservationError("unreachable") from error


def remaining_time(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise ObservationError("unreachable")
    return remaining


class Capture:
    def __init__(self, process, deadline):
        self.process = process
        self.deadline = deadline
        self.output = {"stdout": bytearray(), "stderr": bytearray()}
        self.size = 0
        self.drained = False

    def read_chunk(self, selector, key):
        chunk = os.read(key.fd, 65536)
        if not chunk:
            selector.unregister(key.fileobj)
            return
        self.size += len(chunk)
        if self.size > MAX_OUTPUT_BYTES:
            raise ObservationError("failed")
        self.output[key.data].extend(chunk)

    def collect(self):
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout, selectors.EVENT_READ, "stdout")
            selector.register(self.process.stderr, selectors.EVENT_READ, "stderr")
            while selector.get_map():
                for key, _ in selector.select(remaining_time(self.deadline)):
                    self.read_chunk(selector, key)
            self.process.wait(timeout=max(0.001, self.deadline - time.monotonic()))
        self.drained = True

    def is_empty_directory(self, command):
        return all(
            (
                command == ["a2a", "list", "--json"],
                self.process.returncode == 1,
                bytes(self.output["stderr"]).strip() == EMPTY_DIRECTORY,
            )
        )

    def reply(self, command):
        stdout = self.output["stdout"].decode("utf-8")
        if self.is_empty_directory(command):
            return "{}"
        if self.process.returncode:
            raise ObservationError(
                "unreachable" if self.process.returncode == 255 else "failed"
            )
        return stdout

    def finish(self):
        if not self.drained or self.process.poll() is None:
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        self.process.wait()
        self.process.stdout.close()
        self.process.stderr.close()


def run(host, command, timeout=5):
    deadline = time.monotonic() + timeout
    capture = Capture(start(host, command), deadline)
    try:
        capture.collect()
        return capture.reply(command)
    except (UnicodeDecodeError, subprocess.TimeoutExpired) as error:
        raise ObservationError("failed") from error
    finally:
        capture.finish()
