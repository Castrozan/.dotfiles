import subprocess
import sys
import time

from chatgpt_memory_policy import (
    OPEN_WINDOW_MEMORY_HIGH_BYTES,
    memory_high_for_window_state,
)
from chatgpt_resource_scope import ChatGPTResourceScope
from chatgpt_window_observer import ChatGPTWindowObserver


def control_app(unit_name: str, command: list[str]) -> int:
    scope = ChatGPTResourceScope(unit_name)
    observer = ChatGPTWindowObserver()
    started_at = time.monotonic()
    applied_memory_high = None
    reported_error = False
    child = subprocess.Popen(command)
    while child.poll() is None:
        try:
            grouped = scope.repair_chromium_scope_migration(child.pid)
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
                    f"ChatGPT memory policy: {mode}, MemoryHigh={memory_high}, unit={unit_name}",
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
    return_code = child.returncode
    scope.terminate_remaining_helpers()
    return return_code


if __name__ == "__main__":
    raise SystemExit(control_app(sys.argv[1], sys.argv[2:]))
