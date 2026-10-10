import subprocess
import sys
import time
from collections.abc import Callable

from chatgpt_memory_policy import (
    OPEN_WINDOW_MEMORY_HIGH_BYTES,
    memory_high_for_window_state,
)
from chatgpt_resource_scope import (
    ChatGPTResourceScope,
    ProcessIdentity,
    is_primary_chatgpt_process,
)
from chatgpt_window_observer import ChatGPTWindowObserver


def supervise_app(
    scope: ChatGPTResourceScope, root_process_id: int, is_running: Callable[[], bool]
) -> None:
    observer = ChatGPTWindowObserver()
    started_at = time.monotonic()
    applied_memory_high = None
    reported_error = False
    while is_running():
        try:
            grouped = scope.repair_chromium_scope_migration(root_process_id)
            if observer.refresh_needed or observer.window_open is None:
                observer.refresh(scope.process_ids())
            window_open = observer.window_open if grouped else None
            memory_high = memory_high_for_window_state(
                window_open, time.monotonic() - started_at
            )
            if memory_high != applied_memory_high:
                scope.set_memory_high(memory_high)
                applied_memory_high = memory_high
                mode = (
                    "background"
                    if memory_high < OPEN_WINDOW_MEMORY_HIGH_BYTES
                    else "open"
                )
                print(
                    f"ChatGPT memory policy: {mode}, MemoryHigh={memory_high}, unit={scope.unit_name}",
                    file=sys.stderr,
                    flush=True,
                )
            reported_error = False
        except (OSError, ValueError, subprocess.SubprocessError):
            observer.window_open = None
            observer.refresh_needed = True
            if not reported_error:
                print(
                    "ChatGPT memory policy could not refresh; retaining startup headroom",
                    file=sys.stderr,
                    flush=True,
                )
            reported_error = True
            try:
                scope.set_memory_high(OPEN_WINDOW_MEMORY_HIGH_BYTES)
                applied_memory_high = OPEN_WINDOW_MEMORY_HIGH_BYTES
            except (OSError, subprocess.SubprocessError):
                pass
        try:
            observer.poll(1)
        except (OSError, ValueError):
            observer.disconnect()
    observer.disconnect()


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
