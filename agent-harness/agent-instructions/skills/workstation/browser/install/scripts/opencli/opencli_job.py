import argparse
import os
import re
import signal
import socket
import subprocess
import sys
import tempfile
import uuid

from opencli_owner import register_process, watch_owner
from opencli_processes import stop_process
from opencli_resources import browser_job
from opencli_supervisor import supervise_process


class JobInterrupted(BaseException):
    def __init__(self, number):
        self.number = number


def interrupted(number, frame):
    raise JobInterrupted(number)


def arguments():
    parser = argparse.ArgumentParser(
        description="Run a complete OpenCLI workflow in an owned browser; release every process afterward."
    )
    parser.add_argument("--profile", default="default")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--timeout", type=int, default=900, metavar="SECONDS")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    options = parser.parse_args()
    if options.command[:1] == ["--"]:
        options.command = options.command[1:]
    if not options.command or options.timeout < 1:
        parser.error("Supply a command after -- and a positive timeout")
    return options


def service_command(options):
    command = [
        "systemd-run",
        "--user",
        "--quiet",
        "--pipe",
        "--wait",
        "--collect",
        "--service-type=exec",
        f"--unit=opencli-job-{uuid.uuid4().hex}",
        f"--working-directory={os.getcwd()}",
        f"--property=RuntimeMaxSec={options.timeout + 45}",
        "--property=TimeoutStopSec=10",
        "--property=KillMode=control-group",
    ]
    command.extend(
        f"--setenv={key}"
        for key in os.environ
        if re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", key)
    )
    command.extend(["--", sys.executable, __file__, "--worker", *sys.argv[1:]])
    return command


def transient_service(options):
    command = service_command(options)
    with tempfile.TemporaryDirectory(prefix="opencli-owner-") as directory:
        with socket.socket(socket.AF_UNIX) as listener:
            address = f"{directory}/owner"
            listener.bind(address)
            listener.listen(1)
            listener.settimeout(30)
            environment = dict(os.environ, OPENCLI_JOB_OWNER_SOCKET=address)
            position = command.index("--")
            command.insert(position, "--setenv=OPENCLI_JOB_OWNER_SOCKET")
            return wait_for_service(command, environment, listener)


def wait_for_service(command, environment, listener):
    process = subprocess.Popen(command, env=environment, start_new_session=True)
    try:
        with listener.accept()[0]:
            return process.wait()
    except (JobInterrupted, TimeoutError):
        stop_process(process)
        subprocess.run(
            [
                "systemctl",
                "--user",
                "stop",
                next(
                    value.split("=", 1)[1]
                    for value in command
                    if value.startswith("--unit=")
                ),
            ],
            check=False,
            timeout=15,
        )
        raise


def execute(options):
    if options.worker:
        watch_owner()
    with browser_job(options.profile, options.headed) as environment:
        process = subprocess.Popen(
            options.command, env=environment, start_new_session=True
        )
        try:
            register_process(process)
            return process.wait(timeout=options.timeout)
        finally:
            stop_process(process)


def dispatch(options):
    if options.worker:
        return execute(options)
    if sys.platform == "linux":
        return transient_service(options)
    return supervise_process([sys.executable, __file__, "--worker", *sys.argv[1:]])


def main():
    options = arguments()
    for number in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(number, interrupted)
    try:
        return dispatch(options)
    except JobInterrupted as error:
        return 128 + error.number
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"opencli-run: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
