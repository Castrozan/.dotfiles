import argparse
import fcntl
import hashlib
import os
import pty
import select
import signal
import struct
import sys
import termios
import time
from pathlib import Path

CAST_FILE_MAGIC = b"PCL1"
MAXIMUM_CHUNK_DELAY_SECONDS = 0.5
TERMINAL_READ_BLOCK_SIZE = 65536
CHILD_TERMINATION_GRACE_SECONDS = 0.5


def resolve_terminal_size():
    try:
        size = os.get_terminal_size(sys.stdout.fileno())
        return size.columns, size.lines
    except OSError:
        return 80, 24


def resolve_cast_path(command, capture_seconds, columns, lines):
    signature = "\x00".join(command) + f"\x00{capture_seconds}"
    digest = hashlib.sha1(signature.encode("utf-8", "surrogatepass")).hexdigest()[:12]
    cache_root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    directory = cache_root / "precompute-loop" / f"{digest}-{columns}x{lines}"
    return directory / "cast.bin"


def terminate_child(child_pid, master_fd):
    try:
        os.kill(child_pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    deadline = time.monotonic() + CHILD_TERMINATION_GRACE_SECONDS
    while time.monotonic() < deadline:
        try:
            waited_pid, _ = os.waitpid(child_pid, os.WNOHANG)
        except ChildProcessError:
            break
        if waited_pid == child_pid:
            break
        time.sleep(0.02)
    else:
        try:
            os.kill(child_pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            os.waitpid(child_pid, 0)
        except ChildProcessError:
            pass
    try:
        os.close(master_fd)
    except OSError:
        pass


def capture_command_chunks(command, capture_seconds, columns, lines, echo=True):
    child_pid, master_fd = pty.fork()
    if child_pid == 0:
        os.environ.setdefault("TERM", "xterm-256color")
        try:
            os.execvp(command[0], command)
        except OSError:
            os._exit(127)
    window_size = struct.pack("HHHH", lines, columns, 0, 0)
    fcntl.ioctl(master_fd, termios.TIOCSWINSZ, window_size)
    if echo:
        sys.stdout.write("\033[?25l\033[2J\033[H")
        sys.stdout.flush()
    chunks = []
    started_at = time.monotonic()
    previous_at = started_at
    while time.monotonic() - started_at < capture_seconds:
        readable, _, _ = select.select([master_fd], [], [], 0.2)
        if master_fd not in readable:
            continue
        try:
            data = os.read(master_fd, TERMINAL_READ_BLOCK_SIZE)
        except OSError:
            break
        if not data:
            break
        now = time.monotonic()
        chunks.append((now - previous_at, data))
        previous_at = now
        if echo:
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
    terminate_child(child_pid, master_fd)
    return chunks


def write_cast_file(cast_path, chunks):
    cast_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = cast_path.with_name(f"{cast_path.name}.tmp.{os.getpid()}")
    with open(temporary_path, "wb") as handle:
        handle.write(CAST_FILE_MAGIC)
        handle.write(struct.pack("<I", len(chunks)))
        for delay, data in chunks:
            handle.write(struct.pack("<dI", delay, len(data)))
            handle.write(data)
    os.replace(temporary_path, cast_path)


def load_cast_file(cast_path):
    try:
        with open(cast_path, "rb") as handle:
            if handle.read(len(CAST_FILE_MAGIC)) != CAST_FILE_MAGIC:
                return None
            (chunk_count,) = struct.unpack("<I", handle.read(4))
            chunks = []
            for _ in range(chunk_count):
                header = handle.read(12)
                if len(header) < 12:
                    break
                delay, length = struct.unpack("<dI", header)
                data = handle.read(length)
                if len(data) < length:
                    break
                chunks.append((delay, data))
    except (OSError, struct.error):
        return None
    return chunks


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
            for delay, data in chunks:
                if stop_requested["value"]:
                    break
                if delay > 0:
                    time.sleep(min(delay, MAXIMUM_CHUNK_DELAY_SECONDS))
                output_stream.write(data)
                output_stream.flush()
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()
    finally:
        sys.stdout.write("\033[?25h\033[0m")
        sys.stdout.flush()


def extract_command(raw_command):
    if raw_command and raw_command[0] == "--":
        return raw_command[1:]
    return raw_command


def main():
    parser = argparse.ArgumentParser(prog="precompute-loop")
    parser.add_argument("--seconds", type=float, default=60.0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    arguments = parser.parse_args()
    command = extract_command(arguments.command)
    if not command:
        print("precompute-loop: no command given", file=sys.stderr)
        return 2
    columns, lines = resolve_terminal_size()
    cast_path = resolve_cast_path(command, arguments.seconds, columns, lines)
    chunks = None
    if cast_path.exists() and not arguments.force:
        chunks = load_cast_file(cast_path)
    if not chunks:
        sys.stderr.write(
            f"precompute-loop: recording {arguments.seconds:.0f}s of "
            f"{command[0]} at {columns}x{lines}...\n"
        )
        sys.stderr.flush()
        chunks = capture_command_chunks(command, arguments.seconds, columns, lines)
        if chunks:
            write_cast_file(cast_path, chunks)
    if not chunks:
        print("precompute-loop: nothing captured", file=sys.stderr)
        return 1
    replay_chunks_forever(chunks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
