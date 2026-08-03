"""Unit-level latency test for the herdr pane shell startup path.

Measures the same problem as the herdr e2e benchmark at the shell layer: how
long after spawn a login interactive bash in a fresh PTY processes queued
input, under the herdr pane environment (HERDR_ENV=1). The shell runs the
repo's rc with the flyline line editor loaded, so the probe also answers the
cursor position queries (DSR) that flyline's inline viewport issues during
startup, exactly as herdr's emulator does; flyline issues several, and each
unanswered one blocks for its full timeout, which is the failure mode this
test guards. The bound also catches regressions like flyline versions whose
startup work blocks the editor (v1.3.0's PATH cache scan delayed the first
prompt by ~0.4s; the v1.4.0 upgrade moved it off the critical path).

Runs hermetically: spawns its own PTY, queues an in-band timestamped marker
whose exec time is read from the shell's own output, kills the child. On CI
(no user rc present) it measures a fraction of a second; on the user's machine
it measures the real rc with flyline loaded.
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
CURSOR_POSITION_QUERY = b"\x1b[6n"
CURSOR_POSITION_RESPONSE = b"\x1b[1;1R"
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
    cursor_responses_written = 0
    exec_time_ns = None
    accumulated_output = b""
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
            accumulated_output += output_chunk
            if not input_sent:
                os.write(pty_fd, b"echo UNIT_READY_$(date +%s%N)\n")
                input_sent = True
            query_count = accumulated_output.count(CURSOR_POSITION_QUERY)
            while cursor_responses_written < query_count:
                os.write(pty_fd, CURSOR_POSITION_RESPONSE)
                cursor_responses_written += 1
            if EXEC_MARKER_PATTERN.search(accumulated_output):
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
        "queued command; flyline's startup work must not block the editor "
        "beyond 2.5s when the emulator answers the cursor position query"
    )
