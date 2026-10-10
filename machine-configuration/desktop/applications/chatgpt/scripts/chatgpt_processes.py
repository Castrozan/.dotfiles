import os
from dataclasses import dataclass
from itertools import chain
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


def thread_children(thread: Path) -> list[int]:
    try:
        return [int(child) for child in (thread / "children").read_text().split()]
    except (OSError, ValueError):
        return []


def process_children(process_id: int) -> list[int]:
    try:
        threads = (Path("/proc") / str(process_id) / "task").iterdir()
        return list(chain.from_iterable(thread_children(thread) for thread in threads))
    except OSError:
        return []


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
        pending.extend(process_children(process_id))
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
