import os
import signal
import subprocess
from contextlib import ExitStack

from media_video.contract import VideoError
from media_video.files import create_private_directory


def terminate_process_group(process):
    for process_signal in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process.pid, process_signal)
        except ProcessLookupError:
            pass
        if process_signal == signal.SIGTERM:
            try:
                process.wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                pass
    process.wait(timeout=1)


class CommandRunner:
    def run(self, step, arguments, working_directory, logs_directory, deadline):
        create_private_directory(logs_directory)
        stdout_path = logs_directory / f"{step}.stdout.log"
        stderr_path = logs_directory / f"{step}.stderr.log"
        with ExitStack() as resources:
            logs = []
            for path in (stdout_path, stderr_path):
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                logs.append(resources.enter_context(os.fdopen(descriptor, "wb")))
            deadline.remaining()
            process = subprocess.Popen(
                [str(argument) for argument in arguments],
                cwd=working_directory,
                stdin=subprocess.DEVNULL,
                stdout=logs[0],
                stderr=logs[1],
                start_new_session=True,
            )
            try:
                while True:
                    if any(
                        path.stat().st_size > 64 * 1024 * 1024
                        for path in (stdout_path, stderr_path)
                    ):
                        raise VideoError("process_log_limit_exceeded")
                    try:
                        returncode = process.wait(
                            timeout=min(deadline.remaining(), 0.1)
                        )
                        break
                    except subprocess.TimeoutExpired:
                        continue
                deadline.remaining()
                if returncode != 0:
                    raise VideoError(f"{step}_failed")
            finally:
                terminate_process_group(process)
        return stdout_path
