import json
import os
from pathlib import Path
import signal
import subprocess
import sys

from websockets.sync.server import unix_serve


STATE_DIRECTORY = Path(os.environ["CODEX_TEST_STATE_DIRECTORY"])


def process_identity(process_identifier):
    process = Path(f"/proc/{process_identifier}/stat")
    birth = None
    if process.exists():
        birth = int(process.read_text().rsplit(")", 1)[1].split()[19])
    return {
        "process_identifier": process_identifier,
        "process_group_identifier": os.getpgid(process_identifier),
        "session_identifier": os.getsid(process_identifier),
        "birth": birth,
    }


def record_identity(role, process_identifier):
    destination = STATE_DIRECTORY / f"{role}.json"
    temporary = destination.with_suffix(".temporary")
    temporary.write_text(json.dumps(process_identity(process_identifier)))
    temporary.replace(destination)


def record_interrupt(role):
    def handle_interrupt(signal_number, frame):
        (STATE_DIRECTORY / f"{role}.interrupt").touch()

    return handle_interrupt


def respond_to_initialization(connection):
    for frame in connection:
        request = json.loads(frame)
        if "id" in request:
            connection.send(json.dumps({"id": request["id"], "result": {}}))


def main():
    if "app-server" in sys.argv:
        role = "server"
    elif "--remote" in sys.argv:
        role = "client"
    else:
        role = sys.argv[1]
    signal.signal(signal.SIGINT, record_interrupt(role))
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    record_identity(role, os.getpid())
    if role != "server":
        while True:
            signal.pause()
    record_identity("launcher", os.getppid())
    for worker in ("worker-one", "worker-two"):
        subprocess.Popen([sys.executable, __file__, worker], process_group=0)
    socket_path = os.environ["CODEX_SESSION_SOCKET_PATH"]
    with unix_serve(respond_to_initialization, socket_path) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
