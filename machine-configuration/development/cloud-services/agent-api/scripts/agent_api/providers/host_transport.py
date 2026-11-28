import json
import re
import shlex
import subprocess
import sys

from agent_api.contract import CapabilityError

HOST_TIMEOUT_SECONDS = 120
TRANSFER_TIMEOUT_SECONDS = 600
JOB_PROGRAM = "agent-api-job"
FAILURE_CODE = re.compile(r"^[a-z_]{1,64}$")


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


def job_command(entry, arguments):
    return host_command(entry, [JOB_PROGRAM, *arguments])


def failure_code(stderr):
    lines = stderr.strip().splitlines()
    try:
        code = json.loads(lines[-1])["error"]
    except (IndexError, ValueError, KeyError, TypeError):
        return "host_command_failed"
    if isinstance(code, str) and FAILURE_CODE.match(code):
        return code
    return "host_command_failed"


def host_timeout(stdin, stdout):
    if stdin is subprocess.DEVNULL and stdout is subprocess.PIPE:
        return HOST_TIMEOUT_SECONDS
    return TRANSFER_TIMEOUT_SECONDS


def run_on_host(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE):
    try:
        completed = subprocess.run(
            command,
            stdin=stdin,
            stdout=stdout,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            check=False,
            timeout=host_timeout(stdin, stdout),
        )
    except OSError:
        raise CapabilityError("host_unavailable") from None
    except subprocess.TimeoutExpired:
        raise CapabilityError("host_unresponsive") from None
    sys.stderr.write(completed.stderr)
    if completed.returncode != 0:
        raise CapabilityError(failure_code(completed.stderr))
    return completed.stdout


def run_job(entry, arguments, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE):
    output = run_on_host(job_command(entry, arguments), stdin, stdout)
    if stdout is not subprocess.PIPE:
        return None
    try:
        return json.loads(output)
    except ValueError:
        raise CapabilityError("invalid_host_response") from None
