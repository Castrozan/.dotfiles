import fcntl
import os
import pty
import select
import signal
import struct
import sys
import termios
import time

MAXIMUM_CHUNK_DELAY_SECONDS = 0.5
TERMINAL_READ_BLOCK_SIZE = 65536
CHILD_TERMINATION_GRACE_SECONDS = 0.5


def resolve_terminal_size():
    try:
        size = os.get_terminal_size(sys.stdout.fileno())
        return size.columns, size.lines
    except OSError:
        return 80, 24


def terminate_child(child_pid, master_fd):
    try:
        os.close(master_fd)
    except OSError:
        pass
    for termination_signal in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.kill(child_pid, termination_signal)
        except ProcessLookupError:
            return
        deadline = time.monotonic() + CHILD_TERMINATION_GRACE_SECONDS
        while time.monotonic() < deadline:
            try:
                waited_pid, _ = os.waitpid(child_pid, os.WNOHANG)
            except ChildProcessError:
                return
            if waited_pid == child_pid:
                return
            time.sleep(0.02)


def capture_command_chunks(command, capture_seconds, columns, lines, echo=True):
    child_pid, master_fd = pty.fork()
    if child_pid == 0:
        execute_captured_command(command)
    window_size = struct.pack("HHHH", lines, columns, 0, 0)
    fcntl.ioctl(master_fd, termios.TIOCSWINSZ, window_size)
    echo_terminal_output(echo, initialize=True)
    chunks = []
    started_at = time.monotonic()
    previous_at = started_at
    while time.monotonic() - started_at < capture_seconds:
        data = read_capture_chunk(master_fd)
        if data is None:
            continue
        if not data:
            break
        now = time.monotonic()
        chunks.append((now - previous_at, data))
        previous_at = now
        echo_terminal_output(echo, data)
    terminate_child(child_pid, master_fd)
    return chunks


def execute_captured_command(command):
    os.environ.setdefault("TERM", "xterm-256color")
    try:
        os.execvp(command[0], command)
    except OSError:
        os._exit(127)


def read_capture_chunk(master_fd):
    readable, _, _ = select.select([master_fd], [], [], 0.2)
    if master_fd not in readable:
        return None
    try:
        return os.read(master_fd, TERMINAL_READ_BLOCK_SIZE)
    except OSError:
        return b""


def echo_terminal_output(echo, data=None, initialize=False):
    if not echo:
        return
    if initialize:
        sys.stdout.write("\033[?25l\033[2J\033[H")
        sys.stdout.flush()
    else:
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()


def replay_chunks_forever(chunks):
    output_stream = sys.stdout.buffer
    stop_requested = {"value": False}

    def request_stop(signal_number, frame):
        stop_requested["value"] = True

    for signal_number in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(signal_number, request_stop)
    sys.stdout.write("\033[?25l\033[2J\033[H")
    sys.stdout.flush()
    try:
        while not stop_requested["value"]:
            replay_chunk_cycle(chunks, output_stream, stop_requested)
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()
    finally:
        sys.stdout.write("\033[?25h\033[0m")
        sys.stdout.flush()


def replay_chunk_cycle(chunks, output_stream, stop_requested):
    for delay, data in chunks:
        if stop_requested["value"]:
            break
        if delay > 0:
            time.sleep(min(delay, MAXIMUM_CHUNK_DELAY_SECONDS))
        output_stream.write(data)
        output_stream.flush()
