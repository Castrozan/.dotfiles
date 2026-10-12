import os
import signal
import subprocess
from pathlib import Path

from chatgpt_processes import (
    ProcessIdentity,
    is_primary_chatgpt_process,
    process_cgroup,
    process_tree,
)


class ChatGPTResourceScope:
    def __init__(self, unit_name: str):
        self.unit_name = unit_name
        self.cgroup = process_cgroup(os.getpid())
        if not self.cgroup or Path(self.cgroup).name != unit_name:
            raise ValueError("Resource controller must run inside its own scope")
        self.primary_process = None
        self.pending_migrations = set()
        self.migration_audit_pending = False

    def primary_process_is_alive(self) -> bool:
        return (
            self.primary_process is not None
            and ProcessIdentity.read(self.primary_process.process_id)
            == self.primary_process
        )

    def find_primary_process(self, root_process_id: int):
        return next(
            (
                identity
                for identity in process_tree(root_process_id)
                if is_primary_chatgpt_process(identity)
            ),
            None,
        )

    def membership_is_stable(self) -> bool:
        return (
            not self.pending_migrations
            and process_cgroup(self.primary_process.process_id) == self.cgroup
        )

    def migration_audit_is_required(self) -> bool:
        return self.migration_audit_pending or not self.membership_is_stable()

    def process_needs_attachment(self, identity: ProcessIdentity) -> bool:
        return (
            process_cgroup(identity.process_id) not in (None, self.cgroup)
            and ProcessIdentity.read(identity.process_id) == identity
        )

    def escaped_processes(self, root_process_id: int) -> set[ProcessIdentity]:
        return {
            identity
            for identity in process_tree(root_process_id)
            if self.process_needs_attachment(identity)
        }

    def migration_is_pending(self, identity: ProcessIdentity) -> bool:
        return (
            ProcessIdentity.read(identity.process_id) == identity
            and process_cgroup(identity.process_id) != self.cgroup
        )

    def attach_pending_processes(self) -> None:
        if not self.pending_migrations:
            return
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
                str(len(self.pending_migrations)),
                *(str(identity.process_id) for identity in self.pending_migrations),
            ],
            check=True,
            capture_output=True,
            timeout=3,
        )

    def repair_chromium_scope_migration(self, root_process_id: int) -> bool:
        if not self.primary_process_is_alive():
            self.primary_process = self.find_primary_process(root_process_id)
        if self.primary_process is None:
            return False
        if not self.migration_audit_is_required():
            return True
        self.pending_migrations = self.escaped_processes(root_process_id)
        self.migration_audit_pending = bool(self.pending_migrations)
        self.attach_pending_processes()
        self.pending_migrations = set(
            filter(self.migration_is_pending, self.pending_migrations)
        )
        return self.membership_is_stable()

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
