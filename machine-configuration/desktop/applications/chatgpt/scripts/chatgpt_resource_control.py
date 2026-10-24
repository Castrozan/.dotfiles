import subprocess
import sys
import time
from collections.abc import Callable

from chatgpt_lifecycle_policy import app_should_quit
from chatgpt_processes import ProcessIdentity, is_primary_chatgpt_process
from chatgpt_resource_scope import ChatGPTResourceScope
from chatgpt_window_observer import ChatGPTWindowObserver


class ChatGPTResourceController:
    def __init__(self, scope: ChatGPTResourceScope):
        self.scope = scope
        self.observer = ChatGPTWindowObserver()
        self.started_at = time.monotonic()
        self.windowless_since = None
        self.quit_requested = False
        self.reported_error = False

    def refresh_windows(self):
        if self.observer.refresh_needed or self.observer.window_open is None:
            self.observer.refresh(self.scope.process_ids())

    def windowless_seconds(self, window_open: bool | None, now: float) -> float:
        if window_open is not False:
            self.windowless_since = None
            return 0
        if self.windowless_since is None:
            self.windowless_since = now
        return now - self.windowless_since

    def quit_once(self):
        if self.quit_requested:
            return
        self.scope.quit_app()
        self.quit_requested = True
        print(
            f"ChatGPT window closed; quitting instead of running in the background, unit={self.scope.unit_name}",
            file=sys.stderr,
            flush=True,
        )

    def refresh_policy(self, root_process_id: int):
        grouped = self.scope.repair_chromium_scope_migration(root_process_id)
        self.refresh_windows()
        window_open = self.observer.window_open if grouped else None
        now = time.monotonic()
        if app_should_quit(
            window_open,
            now - self.started_at,
            self.windowless_seconds(window_open, now),
        ):
            self.quit_once()
        self.reported_error = False

    def recover_failure(self):
        self.observer.window_open = None
        self.observer.refresh_needed = True
        self.windowless_since = None
        if not self.reported_error:
            print(
                "ChatGPT window state could not refresh; keeping the app running",
                file=sys.stderr,
                flush=True,
            )
        self.reported_error = True

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
