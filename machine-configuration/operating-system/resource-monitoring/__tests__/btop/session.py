import fcntl
import os
import pty
import re
import select
import struct
import subprocess
import termios
import time
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

    @property
    def plain_output(self):
        return re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", self.output)

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
                plain = self.plain_output
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
