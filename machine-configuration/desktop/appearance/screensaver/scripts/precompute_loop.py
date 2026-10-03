import argparse
import hashlib
import os
import struct
import sys
from pathlib import Path

import precompute_loop_terminal

CAST_FILE_MAGIC = b"PCL1"


def resolve_cast_path(command, capture_seconds, columns, lines):
    signature = "\x00".join(command) + f"\x00{capture_seconds}"
    digest = hashlib.sha1(signature.encode("utf-8", "surrogatepass")).hexdigest()[:12]
    cache_root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    directory = cache_root / "precompute-loop" / f"{digest}-{columns}x{lines}"
    return directory / "cast.bin"


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
    columns, lines = precompute_loop_terminal.resolve_terminal_size()
    cast_path = resolve_cast_path(command, arguments.seconds, columns, lines)
    chunks = load_or_capture_chunks(arguments, command, columns, lines, cast_path)
    if not chunks:
        print("precompute-loop: nothing captured", file=sys.stderr)
        return 1
    precompute_loop_terminal.replay_chunks_forever(chunks)
    return 0


def load_or_capture_chunks(arguments, command, columns, lines, cast_path):
    chunks = None
    if cast_path.exists() and not arguments.force:
        chunks = load_cast_file(cast_path)
    if not chunks:
        sys.stderr.write(
            f"precompute-loop: recording {arguments.seconds:.0f}s of "
            f"{command[0]} at {columns}x{lines}...\n"
        )
        sys.stderr.flush()
        chunks = precompute_loop_terminal.capture_command_chunks(
            command, arguments.seconds, columns, lines
        )
        if chunks:
            write_cast_file(cast_path, chunks)
    return chunks


if __name__ == "__main__":
    sys.exit(main())
