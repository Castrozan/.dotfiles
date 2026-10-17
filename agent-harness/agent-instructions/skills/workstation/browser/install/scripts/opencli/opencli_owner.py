import os
import signal
import socket
import threading

owner_connection = None


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

    threading.Thread(target=wait_for_owner, daemon=True).start()
    return connection


def register_process(process):
    if owner_connection is not None:
        owner_connection.sendall(f"{process.pid}\n".encode())
