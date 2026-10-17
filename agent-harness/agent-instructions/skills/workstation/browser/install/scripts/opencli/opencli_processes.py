import json
import os
import signal
import subprocess
import time
from http.client import HTTPConnection, HTTPException


def stop_process(process):
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except PermissionError:
        if process.poll() is None:
            raise
    process.wait(timeout=5)


def bridge_connected():
    connection = HTTPConnection("127.0.0.1", 19825, timeout=1)
    try:
        connection.request("GET", "/status", headers={"X-OpenCLI": "1"})
        return json.load(connection.getresponse()).get("extensionConnected") is True
    except (OSError, HTTPException, ValueError):
        return False
    finally:
        connection.close()


def wait_for_bridge(processes, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if any(process.poll() is not None for process in processes):
            raise RuntimeError(
                "The owned OpenCLI browser or daemon exited during startup"
            )
        if bridge_connected():
            return
        time.sleep(0.1)
    raise TimeoutError("The owned OpenCLI Browser Bridge did not become ready")
