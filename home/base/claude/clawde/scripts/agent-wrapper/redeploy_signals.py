import signal
import sys

from session_watchdog import terminate_process_tree


class RedeploySignalState:
    def __init__(self) -> None:
        self.resume_requested = False
        self.current_child_process_id: int | None = None


redeploy_signal_state = RedeploySignalState()


def register_current_child_process_id(child_process_id: int | None) -> None:
    redeploy_signal_state.current_child_process_id = child_process_id


def install_exit_signal_handlers() -> None:
    def terminate_cleanly(_signal_number: int, _frame_object) -> None:
        sys.exit(0)

    for signal_number in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(signal_number, terminate_cleanly)


def request_resume_restart_now() -> None:
    redeploy_signal_state.resume_requested = True
    child_process_id = redeploy_signal_state.current_child_process_id
    if child_process_id is not None:
        terminate_process_tree(child_process_id)


def install_redeploy_signal_handler() -> None:
    def handle_redeploy_signal(_signal_number: int, _frame_object) -> None:
        request_resume_restart_now()

    signal.signal(signal.SIGUSR1, handle_redeploy_signal)
