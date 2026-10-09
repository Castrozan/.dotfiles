import os
import signal
import subprocess
import sys
import time
from contextlib import contextmanager


@contextmanager
def foreground_process_group(process_group):
    previous_process_group = None
    previous_stop_handler = signal.getsignal(signal.SIGTTOU)
    try:
        if os.isatty(0) and os.tcgetpgrp(0) == os.getpgrp():
            previous_process_group = os.getpgrp()
            signal.signal(signal.SIGTTOU, signal.SIG_IGN)
            try:
                os.tcsetpgrp(0, process_group)
                os.killpg(process_group, signal.SIGCONT)
            except ProcessLookupError:
                pass
        yield
    finally:
        if previous_process_group is not None:
            os.tcsetpgrp(0, previous_process_group)
            signal.signal(signal.SIGTTOU, previous_stop_handler)


def wait_for_process_group_exit(process_group):
    while True:
        try:
            os.killpg(process_group, 0)
        except ProcessLookupError:
            return
        time.sleep(0.05)


def run_owned_process_group(file_descriptor, command):
    child = None
    pending_signal = None

    def forward_termination_signal(received_signal, frame):
        nonlocal pending_signal
        if child is None:
            pending_signal = received_signal
            return
        try:
            os.killpg(child.pid, received_signal)
        except ProcessLookupError:
            pass

    for termination_signal in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(termination_signal, forward_termination_signal)
    with os.fdopen(file_descriptor, "rb"):
        child = subprocess.Popen(command, pass_fds=(file_descriptor,), process_group=0)
        if pending_signal is not None:
            forward_termination_signal(pending_signal, None)
        try:
            with foreground_process_group(child.pid):
                exit_status = child.wait()
                wait_for_process_group_exit(child.pid)
        finally:
            child.wait()
            wait_for_process_group_exit(child.pid)
    return exit_status if exit_status >= 0 else 128 - exit_status


def main():
    try:
        return run_owned_process_group(int(sys.argv[1]), sys.argv[2:])
    except (OSError, ValueError) as error:
        print(f"error: exclusive run scope unavailable: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
