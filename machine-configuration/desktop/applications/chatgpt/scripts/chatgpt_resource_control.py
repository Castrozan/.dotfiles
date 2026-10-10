import subprocess
import sys
import time
from collections.abc import Callable

from chatgpt_memory_policy import (
    OPEN_WINDOW_MEMORY_HIGH_BYTES,
    memory_high_for_window_state,
)
from chatgpt_processes import ProcessIdentity, is_primary_chatgpt_process
from chatgpt_resource_scope import ChatGPTResourceScope
from chatgpt_window_observer import ChatGPTWindowObserver


class ChatGPTResourceController:
    def __init__(self, scope: ChatGPTResourceScope):
        self.scope = scope
        self.observer = ChatGPTWindowObserver()
        self.started_at = time.monotonic()
        self.applied_memory_high = None
        self.reported_error = False

    def refresh_windows(self):
        if self.observer.refresh_needed or self.observer.window_open is None:
            self.observer.refresh(self.scope.process_ids())

    def apply_memory_high(self, memory_high: int):
        if memory_high == self.applied_memory_high:
            return
        self.scope.set_memory_high(memory_high)
        self.applied_memory_high = memory_high
        mode = "background" if memory_high < OPEN_WINDOW_MEMORY_HIGH_BYTES else "open"
        print(
            f"ChatGPT memory policy: {mode}, MemoryHigh={memory_high}, unit={self.scope.unit_name}",
            file=sys.stderr,
            flush=True,
        )

    def refresh_policy(self, root_process_id: int):
        grouped = self.scope.repair_chromium_scope_migration(root_process_id)
        self.refresh_windows()
        window_open = self.observer.window_open if grouped else None
        memory_high = memory_high_for_window_state(
            window_open, time.monotonic() - self.started_at
        )
        self.apply_memory_high(memory_high)
        self.reported_error = False

    def recover_failure(self):
        self.observer.window_open = None
        self.observer.refresh_needed = True
        if not self.reported_error:
            print(
                "ChatGPT memory policy could not refresh; retaining startup headroom",
                file=sys.stderr,
                flush=True,
            )
        self.reported_error = True
        try:
            self.scope.set_memory_high(OPEN_WINDOW_MEMORY_HIGH_BYTES)
            self.applied_memory_high = OPEN_WINDOW_MEMORY_HIGH_BYTES
        except (OSError, subprocess.SubprocessError):
            pass

    def poll(self):
        try:
            self.observer.poll(1)
        except (OSError, ValueError):
            self.observer.disconnect()


def supervise_app(
    scope: ChatGPTResourceScope, root_process_id: int, is_running: Callable[[], bool]
) -> None:
    controller = ChatGPTResourceController(scope)
    while is_running():
        try:
            controller.refresh_policy(root_process_id)
        except (OSError, ValueError, subprocess.SubprocessError):
            controller.recover_failure()
        controller.poll()
    controller.observer.disconnect()


def control_app(unit_name: str, command: list[str]) -> int:
    scope = ChatGPTResourceScope(unit_name)
    child = subprocess.Popen(command)
    supervise_app(scope, child.pid, lambda: child.poll() is None)
    return_code = child.returncode
    scope.terminate_remaining_helpers()
    return return_code


def attach_running_app(unit_name: str, process_id: int) -> int:
    identity = ProcessIdentity.read(process_id)
    if identity is None or not is_primary_chatgpt_process(identity):
        raise ValueError("Attachment requires the running ChatGPT main process")
    scope = ChatGPTResourceScope(unit_name)
    supervise_app(
        scope, process_id, lambda: ProcessIdentity.read(process_id) == identity
    )
    return 0


if __name__ == "__main__":
    if sys.argv[2] == "--attach-process":
        raise SystemExit(attach_running_app(sys.argv[1], int(sys.argv[3])))
    raise SystemExit(control_app(sys.argv[1], sys.argv[2:]))
