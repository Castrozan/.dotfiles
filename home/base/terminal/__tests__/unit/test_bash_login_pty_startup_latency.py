"""Unit-level latency test for the herdr pane shell startup path.

Measures the same problem as the herdr e2e benchmark at the shell layer: how
long after spawn a login interactive bash in a fresh PTY processes queued
input, under the herdr pane environment (HERDR_ENV=1). This is the regression
guard for the flyline gate in home/base/terminal/bash.nix: flyline's inline
viewport issues a cursor position query (DSR) and blocks until a timeout when
the terminal does not answer, and herdr's emulator does not answer it, so an
ungated rc makes the first keystroke land 1.4-4.5s late in every new pane.
With the gate in place the herdr-env shell skips flyline and stays fast.

Runs hermetically: spawns its own PTY, queues an in-band timestamped marker
whose exec time is read from the shell's own output, kills the child. On CI
(no user rc present) it measures a fraction of a second; on the user's machine
it measures the real rc with the gate applied.
"""

from __future__ import annotations

import fcntl
import os
import pty
import re
import select
import shutil
import struct
import termios
import time

import pytest

EXEC_MARKER_PATTERN = re.compile(rb"UNIT_READY_(\d{16,19})")
STARTUP_LATENCY_BOUND_SECONDS = 2.5


def login_shell_path() -> str:
    configured_shell = os.environ.get("SHELL", "")
    if configured_shell and os.path.basename(configured_shell).startswith("bash"):
        return configured_shell
    return shutil.which("bash") or "/bin/bash"


def herdr_pane_environment() -> dict[str, str]:
    home = os.path.expanduser("~")
    aliases_path = os.path.join(home, ".dotfiles/home/base/terminal/shell/aliases.sh")
    environment = {
        "HOME": home,
        "TERM": "xterm-256color",
        "SHELL": login_shell_path(),
        "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        "TERM_PROGRAM": "WezTerm",
        "TERM_PROGRAM_VERSION": "test",
        "HERDR_ENV": "1",
        "HERDR_PANE_ID": "test:pane",
        "HERDR_SOCKET_PATH": "/tmp/herdr-test.sock",
        "HERDR_TAB_ID": "test:tab",
        "HERDR_WORKSPACE_ID": "test:workspace",
    }
    if os.path.isfile(aliases_path):
        environment["BASH_ENV"] = aliases_path
    return environment


def measure_herdr_pane_writable_latency() -> float:
    shell = login_shell_path()
    child_pid, pty_fd = pty.fork()
    if child_pid == 0:
        os.environ.clear()
        os.environ.update(herdr_pane_environment())
        os.execv(shell, ["-bash", "-l", "-i"])
    fcntl.ioctl(pty_fd, termios.TIOCSWINSZ, struct.pack("HHHH", 43, 168, 0, 0))
    spawn_time_ns = time.monotonic_ns()
    input_sent = False
    exec_time_ns = None
    deadline_ns = spawn_time_ns + 15_000_000_000
    try:
        while time.monotonic_ns() < deadline_ns:
            readable, _, _ = select.select([pty_fd], [], [], 0.02)
            if not readable:
                continue
            try:
                output_chunk = os.read(pty_fd, 8192)
            except OSError:
                break
            if not output_chunk:
                break
            if not input_sent:
                os.write(pty_fd, b"echo UNIT_READY_$(date +%s%N)\n")
                input_sent = True
            if EXEC_MARKER_PATTERN.search(output_chunk):
                exec_time_ns = time.monotonic_ns()
                break
    finally:
        try:
            os.kill(child_pid, 9)
        except ProcessLookupError:
            pass
        os.close(pty_fd)
    if exec_time_ns is None:
        pytest.fail("the herdr-pane shell never executed the queued marker")
    return (exec_time_ns - spawn_time_ns) / 1_000_000_000


def test_herdr_pane_shell_processes_first_command_within_bound():
    latency = measure_herdr_pane_writable_latency()
    assert latency < STARTUP_LATENCY_BOUND_SECONDS, (
        f"herdr-pane login shell took {latency:.2f}s to process the first "
        "queued command; the flyline DSR block reproduces as >2.5s when the "
        "HERDR_ENV gate in home/base/terminal/bash.nix is missing"
    )
