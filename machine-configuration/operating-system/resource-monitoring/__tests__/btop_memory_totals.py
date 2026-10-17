import fcntl
import os
import pty
import re
import select
import struct
import subprocess
import sys
import tempfile
import termios
import time
from pathlib import Path
from typing import NamedTuple


class MemoryTotals(NamedTuple):
    visible_process_percent: float
    all_process_percent: float
    system_used_percent: float


class BtopSession:
    def __init__(
        self,
        binary,
        directory,
        shown_boxes="cpu mem proc",
        columns=160,
        rows=30,
        update_ms=60000,
    ):
        self.configuration = directory / "btop.conf"
        self.configuration.write_text(
            f'shown_boxes = "{shown_boxes}"\n'
            f"update_ms = {update_ms}\n"
            "show_disks = False\n"
            "proc_mem_bytes = False\n"
            'proc_sorting = "memory"\n'
            "proc_aggregate = True\n"
        )
        self.master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", rows, columns, 0, 0))
        self.process = subprocess.Popen(
            [binary, "--config", str(self.configuration)],
            stdin=slave,
            stdout=slave,
            stderr=slave,
            env={
                **os.environ,
                "TERM": "xterm-256color",
                "LANG": "C.UTF-8",
                "XDG_CONFIG_HOME": str(directory),
            },
            start_new_session=True,
        )
        os.close(slave)
        self.output = ""

    def read_summary(self, timeout=5):
        deadline = time.monotonic() + timeout
        self.output = ""
        matches = []
        while time.monotonic() < deadline:
            if select.select([self.master], [], [], 0.1)[0]:
                try:
                    self.output += os.read(self.master, 65536).decode(errors="replace")
                except OSError:
                    break
                plain = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", self.output)
                matches = re.findall(
                    r"Visible(?: RSS)?: ([\d.]+)% +All(?: RSS)?: ([\d.]+)% +(?:System )?used: ([\d.]+)%",
                    plain,
                )
            elif matches:
                return MemoryTotals(*(float(value) for value in matches[-1]))
            if self.process.poll() is not None:
                break
        raise AssertionError(f"Missing memory totals: {self.output[-2000:]}")

    def send(self, keys):
        while select.select([self.master], [], [], 0)[0]:
            os.read(self.master, 65536)
        os.write(self.master, keys)
        time.sleep(0.1)

    def close(self):
        self.process.terminate()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        os.close(self.master)


def verify(binary):
    with tempfile.TemporaryDirectory(prefix="btop-memory-totals-") as directory:
        session = BtopSession(binary, Path(directory))
        try:
            visible, all_processes, system_used = session.read_summary()
            assert 0 < visible <= all_processes
            assert 0 < system_used <= 100
            session.send(b"f")
            session.send(b"z")
            session.send(b"z")
            session.send(b"z")
            session.send(b"z")
            session.send(b"z")
            session.send(b"\n")
            filtered = session.read_summary()
            assert filtered == MemoryTotals(0.0, all_processes, system_used), filtered
            session.send(b"\x1b[3~")
            restored = session.read_summary()
            assert restored == MemoryTotals(visible, all_processes, system_used), (
                restored
            )
            session.send(b"e")
            tree = session.read_summary()
            assert 0 <= tree.visible_process_percent
            assert 0 < tree.all_process_percent
            assert 0 < tree.system_used_percent <= 100
            session.send(b"f")
            for character in b"zzzzz":
                session.send(bytes([character]))
            session.send(b"\n")
            filtered_tree = session.read_summary()
            expected_tree = MemoryTotals(
                0.0, tree.all_process_percent, tree.system_used_percent
            )
            assert filtered_tree == expected_tree, (filtered_tree, expected_tree)
            session.send(b"2")
            hidden_memory = session.read_summary()
            assert hidden_memory.visible_process_percent == 0.0
            assert hidden_memory.system_used_percent > 0
        finally:
            session.close()
        session = BtopSession(binary, Path(directory), shown_boxes="proc", columns=44)
        try:
            narrow = session.read_summary()
            assert 0 < narrow.visible_process_percent <= narrow.all_process_percent
            assert 0 < narrow.system_used_percent <= 100
        finally:
            session.close()
    print(
        "Verified visible, global, filtered, tree, hidden-panel, and narrow memory totals"
    )


if __name__ == "__main__":
    verify(sys.argv[1])
