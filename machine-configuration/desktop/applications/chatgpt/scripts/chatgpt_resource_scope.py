import os
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProcessIdentity:
    process_id: int
    start_ticks: int

    @classmethod
    def read(cls, process_id: int):
        try:
            fields = (
                (Path("/proc") / str(process_id) / "stat")
                .read_text()
                .rsplit(") ", 1)[1]
                .split()
            )
            return cls(process_id, int(fields[19]))
        except (OSError, ValueError, IndexError):
            return None


def process_tree(root_process_id: int) -> set[ProcessIdentity]:
    pending = [root_process_id]
    processes = set()
    visited = set()
    while pending:
        process_id = pending.pop()
        if process_id in visited:
            continue
        visited.add(process_id)
        identity = ProcessIdentity.read(process_id)
        if identity is None:
            continue
        processes.add(identity)
        try:
            threads = (Path("/proc") / str(process_id) / "task").iterdir()
            for thread in threads:
                try:
                    pending.extend(
                        int(child)
                        for child in (thread / "children").read_text().split()
                    )
                except (OSError, ValueError):
                    continue
        except OSError:
            continue
    return processes


def process_cgroup(process_id: int) -> str | None:
    try:
        return (
            (Path("/proc") / str(process_id) / "cgroup")
            .read_text()
            .strip()
            .split("0::", 1)[1]
        )
    except (OSError, IndexError):
        return None


def is_primary_chatgpt_process(identity: ProcessIdentity) -> bool:
    path = Path("/proc") / str(identity.process_id)
    try:
        return (
            os.readlink(path / "exe").endswith("/lib/chatgpt/ChatGPT")
            and b"--type=" not in (path / "cmdline").read_bytes()
        )
    except OSError:
        return False


class ChatGPTResourceScope:
    def __init__(self, unit_name: str):
        self.unit_name = unit_name
        self.cgroup = process_cgroup(os.getpid())
        if not self.cgroup or Path(self.cgroup).name != unit_name:
            raise ValueError("Resource controller must run inside its own scope")
        self.primary_process = None
        self.pending_migrations = set()

    def repair_chromium_scope_migration(self, root_process_id: int) -> bool:
        if (
            self.primary_process is None
            or ProcessIdentity.read(self.primary_process.process_id)
            != self.primary_process
        ):
            self.primary_process = next(
                (
                    identity
                    for identity in process_tree(root_process_id)
                    if is_primary_chatgpt_process(identity)
                ),
                None,
            )
        if self.primary_process is None:
            return False
        if (
            process_cgroup(self.primary_process.process_id) == self.cgroup
            and not self.pending_migrations
        ):
            return True
        escaped = [
            identity
            for identity in process_tree(root_process_id)
            if process_cgroup(identity.process_id) not in (None, self.cgroup)
            and ProcessIdentity.read(identity.process_id) == identity
        ]
        self.pending_migrations = set(escaped)
        if escaped:
            subprocess.run(
                [
                    "busctl",
                    "--user",
                    "call",
                    "org.freedesktop.systemd1",
                    "/org/freedesktop/systemd1",
                    "org.freedesktop.systemd1.Manager",
                    "AttachProcessesToUnit",
                    "ssau",
                    self.unit_name,
                    "",
                    str(len(escaped)),
                    *(str(identity.process_id) for identity in escaped),
                ],
                check=True,
                capture_output=True,
                timeout=3,
            )
        self.pending_migrations = {
            identity
            for identity in self.pending_migrations
            if ProcessIdentity.read(identity.process_id) == identity
            and process_cgroup(identity.process_id) != self.cgroup
        }
        return (
            not self.pending_migrations
            and process_cgroup(self.primary_process.process_id) == self.cgroup
        )

    def process_ids(self) -> set[int]:
        return {
            int(value)
            for value in (
                Path("/sys/fs/cgroup") / self.cgroup.lstrip("/") / "cgroup.procs"
            )
            .read_text()
            .split()
        }

    def set_memory_high(self, memory_high_bytes: int) -> None:
        subprocess.run(
            [
                "systemctl",
                "--user",
                "set-property",
                "--runtime",
                self.unit_name,
                f"MemoryHigh={memory_high_bytes}",
            ],
            check=True,
            capture_output=True,
            timeout=3,
        )

    def terminate_remaining_helpers(self) -> None:
        for process_id in self.process_ids() - {os.getpid()}:
            try:
                descriptor = os.pidfd_open(process_id)
                try:
                    if process_cgroup(process_id) == self.cgroup:
                        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
                finally:
                    os.close(descriptor)
            except OSError:
                continue
