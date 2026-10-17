import os
import signal
import socket
import subprocess
import tempfile

from opencli_processes import stop_process


def supervise_process(arguments):
    with tempfile.TemporaryDirectory(prefix="opencli-owner-") as directory:
        with socket.socket(socket.AF_UNIX) as listener:
            address = f"{directory}/owner"
            listener.bind(address)
            listener.listen(1)
            listener.settimeout(30)
            environment = dict(os.environ, OPENCLI_JOB_OWNER_SOCKET=address)
            process = subprocess.Popen(
                arguments, env=environment, start_new_session=True
            )
            connection = None
            try:
                connection = listener.accept()[0]
                return process.wait()
            finally:
                blocked = {signal.SIGTERM, signal.SIGINT, signal.SIGHUP}
                previous = signal.pthread_sigmask(signal.SIG_BLOCK, blocked)
                try:
                    if process.poll() is None:
                        stop_process(process)
                    if connection is not None:
                        cleanup_registered_processes(connection)
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK, previous)


def cleanup_registered_processes(connection):
    with connection:
        payload = bytearray()
        while chunk := connection.recv(4096):
            payload.extend(chunk)
    for identifier in set(payload.decode().splitlines()):
        if identifier.isdigit():
            try:
                os.killpg(int(identifier), signal.SIGKILL)
            except ProcessLookupError:
                pass
