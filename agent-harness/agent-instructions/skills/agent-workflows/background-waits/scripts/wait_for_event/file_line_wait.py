from __future__ import annotations

import os
import select
import subprocess
import sys
import time

from .process_exit_wait import seconds_left_before

READ_CHUNK_BYTES = 65536
DARWIN_KQUEUE_TAIL = "/usr/bin/tail"


def following_tail_executable():
    return DARWIN_KQUEUE_TAIL if sys.platform == "darwin" else "tail"


def _first_matching_line(complete_lines, line_pattern):
    for line in complete_lines:
        decoded_line = line.decode(errors="replace")
        if line_pattern.search(decoded_line):
            return decoded_line
    return None


class _FollowedFile:
    def __init__(self, file_path):
        self.tail_process = subprocess.Popen(
            [following_tail_executable(), "-F", "-n", "+1", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        self.output_descriptor = self.tail_process.stdout.fileno()
        self.unfinished_line = b""

    def next_complete_lines(self, timeout_seconds):
        readable, _, _ = select.select(
            [self.output_descriptor], [], [], timeout_seconds
        )
        if not readable:
            return []
        chunk = os.read(self.output_descriptor, READ_CHUNK_BYTES)
        if not chunk:
            raise EOFError
        *complete_lines, self.unfinished_line = (self.unfinished_line + chunk).split(
            b"\n"
        )
        return complete_lines

    def stop(self):
        self.tail_process.kill()
        self.tail_process.wait()


def first_line_matching(file_path, line_pattern, timeout_seconds):
    deadline = None if timeout_seconds is None else time.monotonic() + timeout_seconds
    followed_file = _FollowedFile(file_path)
    try:
        return _read_until_match(followed_file, line_pattern, deadline)
    finally:
        followed_file.stop()


def _read_until_match(followed_file, line_pattern, deadline):
    while seconds_left_before(deadline) != 0.0:
        matching_line = _first_matching_line(
            followed_file.next_complete_lines(seconds_left_before(deadline)),
            line_pattern,
        )
        if matching_line is not None:
            return matching_line
    return None
