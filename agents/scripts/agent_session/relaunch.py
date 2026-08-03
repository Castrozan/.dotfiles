import json
import os
import select
import signal
import subprocess
import sys
from argparse import Namespace
from pathlib import Path

from . import restart_lock
from .processes import wait_for_agent_session_exit
from .relaunch_transport import (
    relaunch_target_is_ready,
    resume_and_continue_session,
    wait_for_relaunch_target_idle,
)

RESTART_LAUNCHER_READY_SECONDS = 5
RESTART_LAUNCHER_STOP_SECONDS = 5


def multiplexer_context_from_environment() -> tuple[str, str] | None:
    herdr_pane_identifier = os.environ.get("HERDR_PANE_ID")
    if herdr_pane_identifier:
        return "herdr", herdr_pane_identifier
    return None


def restart_launcher_command(
    process_identifier: int,
    multiplexer_name: str,
    pane_identifier: str,
    resume_command: list[str],
    acquired_restart_lock: restart_lock.RestartLock,
    ready_file_descriptor: int,
) -> list[str]:
    script_path = Path(__file__).resolve().parents[1] / "agent_session_control.py"
    return [
        sys.executable,
        str(script_path),
        "launch",
        "--process-identifier",
        str(process_identifier),
        "--multiplexer-name",
        multiplexer_name,
        "--pane-identifier",
        pane_identifier,
        "--resume-command",
        json.dumps(resume_command),
        "--restart-lock-path",
        str(acquired_restart_lock.path),
        "--restart-lock-owner-token",
        acquired_restart_lock.owner_token,
        "--restart-launcher-ready-file-descriptor",
        str(ready_file_descriptor),
    ]


def restart_launcher_is_ready(ready_file_descriptor: int) -> bool:
    ready_file_descriptors, _, _ = select.select(
        [ready_file_descriptor], [], [], RESTART_LAUNCHER_READY_SECONDS
    )
    return bool(ready_file_descriptors) and os.read(ready_file_descriptor, 1) == b"1"


def terminate_restart_launcher(launched_process: subprocess.Popen) -> None:
    try:
        os.killpg(launched_process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        launched_process.wait(timeout=RESTART_LAUNCHER_STOP_SECONDS)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(launched_process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        launched_process.wait()


def launch_restart_launcher(
    process_identifier: int,
    multiplexer_name: str,
    pane_identifier: str,
    resume_command: list[str],
    acquired_restart_lock: restart_lock.RestartLock,
) -> int | None:
    ready_reader_file_descriptor, ready_writer_file_descriptor = os.pipe()
    try:
        try:
            launched_process = subprocess.Popen(
                restart_launcher_command(
                    process_identifier,
                    multiplexer_name,
                    pane_identifier,
                    resume_command,
                    acquired_restart_lock,
                    ready_writer_file_descriptor,
                ),
                pass_fds=(ready_writer_file_descriptor,),
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            return None
        finally:
            os.close(ready_writer_file_descriptor)
        if restart_launcher_is_ready(ready_reader_file_descriptor):
            return launched_process.pid
        terminate_restart_launcher(launched_process)
        return None
    finally:
        os.close(ready_reader_file_descriptor)


def signal_restart_launcher_ready(ready_file_descriptor: int) -> bool:
    try:
        os.write(ready_file_descriptor, b"1")
    except OSError:
        return False
    return True


def relaunch_after_exit(arguments: Namespace) -> int:
    acquired_restart_lock = restart_lock.RestartLock(
        Path(arguments.restart_lock_path), arguments.restart_lock_owner_token
    )
    if acquired_restart_lock.path != restart_lock.restart_lock_path_for(
        arguments.process_identifier
    ):
        print("Restart launcher received an invalid lock path.")
        return 1
    try:
        if not restart_lock.restart_lock_is_owned(acquired_restart_lock):
            print("Restart launcher no longer owns this restart lock.")
            return 1
        if not relaunch_target_is_ready(
            arguments.multiplexer_name, arguments.pane_identifier
        ):
            print("Restart launcher could not reach the target pane.")
            return 1
        if not signal_restart_launcher_ready(
            arguments.restart_launcher_ready_file_descriptor
        ):
            return 1
        if not wait_for_agent_session_exit(arguments.process_identifier):
            return 1
        if not wait_for_relaunch_target_idle(
            arguments.multiplexer_name, arguments.pane_identifier
        ):
            print(
                "Restart launcher timed out waiting for the target pane to become idle."
            )
            return 1
        resume_command = json.loads(arguments.resume_command)
        continuation_succeeded = False

        def resume_and_continue() -> None:
            nonlocal continuation_succeeded
            continuation_succeeded = resume_and_continue_session(
                arguments.pane_identifier,
                resume_command,
            )

        relaunch_completed = restart_lock.execute_while_restart_lock_is_owned(
            acquired_restart_lock,
            resume_and_continue,
        )
        if not relaunch_completed:
            print("Restart launcher no longer owns this restart lock.")
            return 1
        if not continuation_succeeded:
            print("Restart launcher timed out waiting for the resumed session.")
            return 1
        return 0
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"Restart launcher could not resume the session: {error}")
        return 1
    finally:
        restart_lock.release_restart_lock(acquired_restart_lock)
