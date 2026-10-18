import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from agent_api.contract import (
    MAXIMUM_ARTIFACT_BYTES,
    MAXIMUM_RESULT_BYTES,
    CapabilityError,
)


class WorkerExecutor:
    def execute(self, directory, timeout_seconds):
        entrypoint = Path(__file__).resolve().parents[1] / "agent_api_cli.py"
        environment = dict(
            os.environ,
            OMP_NUM_THREADS="2",
            OPENBLAS_NUM_THREADS="2",
            PYTHONDONTWRITEBYTECODE="1",
        )
        deadline = time.monotonic() + timeout_seconds
        with (directory / "worker.log").open("wb") as log:
            process = subprocess.Popen(
                [sys.executable, str(entrypoint), "worker", str(directory)],
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=log,
                start_new_session=True,
                env=environment,
            )
            try:
                self.wait(process, directory, deadline)
            except BaseException:
                self.stop(process)
                raise
        result_path = directory / "result.json"
        if (
            not result_path.is_file()
            or result_path.stat().st_size > MAXIMUM_RESULT_BYTES
        ):
            raise CapabilityError("worker_failed")
        try:
            result = json.loads(result_path.read_bytes())
        except (ValueError, UnicodeError):
            raise CapabilityError("invalid_worker_response") from None
        if result.get("status") != "succeeded":
            raise CapabilityError(result.get("error", "execution_failed"))
        return result["output"]

    def wait(self, process, directory, deadline):
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CapabilityError("deadline_exceeded")
            sizes = {
                path.name: path.stat().st_size
                for path in directory.iterdir()
                if path.is_file()
            }
            if (
                sizes.get("worker.log", 0) > MAXIMUM_RESULT_BYTES
                or sum(sizes.values()) > MAXIMUM_ARTIFACT_BYTES
            ):
                raise CapabilityError("artifact_too_large")
            try:
                process.wait(timeout=min(0.25, remaining))
                return
            except subprocess.TimeoutExpired:
                pass

    def stop(self, process):
        try:
            os.killpg(process.pid, signal.SIGINT)
            process.wait(timeout=5)
        except ProcessLookupError:
            pass
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
