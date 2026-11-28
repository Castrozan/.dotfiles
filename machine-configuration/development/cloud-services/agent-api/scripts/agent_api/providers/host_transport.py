import shlex
import subprocess
import sys

from agent_api.contract import CapabilityError

HOST_TIMEOUT_SECONDS = 120


def host_command(entry, arguments):
    if entry["transport"] == "local":
        return arguments
    return [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        entry["ssh_alias"],
        "--",
        shlex.join(arguments),
    ]


def run_on_host(entry, arguments):
    try:
        completed = subprocess.run(
            host_command(entry, arguments),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
            timeout=HOST_TIMEOUT_SECONDS,
        )
    except OSError:
        raise CapabilityError("host_unavailable") from None
    except subprocess.TimeoutExpired:
        raise CapabilityError("host_unresponsive") from None
    sys.stderr.write(completed.stderr)
    return completed
