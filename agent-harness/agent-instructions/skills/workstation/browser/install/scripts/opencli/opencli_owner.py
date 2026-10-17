import os
import signal
import socket
import subprocess
import sys
import threading
from contextlib import contextmanager
from pathlib import Path

from opencli_processes import stop_process

owner_connection = None
TERMINATION_SIGNALS = {signal.SIGTERM, signal.SIGINT, signal.SIGHUP}


@contextmanager
def blocked_termination():
    previous = signal.pthread_sigmask(signal.SIG_BLOCK, TERMINATION_SIGNALS)
    try:
        yield previous
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous)


@contextmanager
def owned_process(arguments, environment, output=None, pass_fds=()):
    if owner_connection is None:
        raise RuntimeError("Owned process startup requires worker supervision")
    process = None
    try:
        with blocked_termination() as previous:
            descriptor = owner_connection.fileno()
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(Path(__file__).with_name("opencli_exec.py")),
                    str(descriptor),
                    ",".join(str(int(number)) for number in sorted(previous)),
                    *arguments,
                ],
                env=environment,
                stdout=output,
                stderr=output,
                pass_fds=(descriptor, *pass_fds),
                start_new_session=True,
            )
        yield process
    finally:
        if process is not None:
            with blocked_termination():
                stop_process(process)


def watch_owner():
    global owner_connection
    address = os.environ["OPENCLI_JOB_OWNER_SOCKET"]
    connection = socket.socket(socket.AF_UNIX)
    connection.settimeout(5)
    connection.connect(address)
    connection.settimeout(None)
    owner_connection = connection

    def wait_for_owner():
        try:
            connection.recv(1)
        finally:
            connection.close()
            os.kill(os.getpid(), signal.SIGTERM)

    with blocked_termination():
        threading.Thread(target=wait_for_owner, daemon=True).start()
    return connection
