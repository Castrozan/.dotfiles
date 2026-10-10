import argparse
import fcntl
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def current_system():
    system = Path("/run/current-system")
    return str(system.resolve()) if system.exists() else None


def write_result(state_directory, result):
    temporary = state_directory / "rebuild-result.json.tmp"
    temporary.write_text(json.dumps(result, indent=2) + "\n")
    temporary.replace(state_directory / "rebuild-result.json")


def desired_system(configuration):
    evaluation = subprocess.run(
        [
            os.environ["SYSTEM_REBUILD_LOCK_GUARD"],
            "nix",
            "eval",
            "--raw",
            "--no-write-lock-file",
            configuration,
        ],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if evaluation.returncode != 0:
        raise RuntimeError(
            evaluation.stderr.strip() or "configuration evaluation failed"
        )
    system = evaluation.stdout.strip()
    if not system.startswith("/nix/store/") or "\n" in system:
        raise RuntimeError("configuration did not evaluate to a system store path")
    return system


def activate_configuration(configuration, result):
    result["desired_system"] = desired_system(configuration)
    if result["desired_system"] == result["system_before"]:
        result["status"] = "unchanged"
        return 0
    return subprocess.run(["rebuild"], check=False).returncode


def run_rebuild(state_directory, configuration):
    result = {
        "status": "running",
        "process_id": os.getpid(),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "system_before": current_system(),
    }
    write_result(state_directory, result)
    try:
        exit_code = activate_configuration(configuration, result)
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        exit_code = 1
        result["error"] = str(error)
    system_after = current_system()
    exit_code = _validate_activated_system(exit_code, system_after, result)
    status = "succeeded" if exit_code == 0 else "failed"
    if result["status"] == "unchanged" and exit_code == 0:
        status = "unchanged"
    result.update(
        status=status,
        exit_code=exit_code,
        completed_at=datetime.now(timezone.utc).isoformat(),
        system_after=system_after,
    )
    write_result(state_directory, result)
    return exit_code


def _validate_activated_system(exit_code, system_after, result):
    if exit_code != 0 or system_after == result["desired_system"]:
        return exit_code
    result["error"] = "live system differs from the evaluated configuration"
    return 1


def launch_rebuild(state_directory, configuration):
    state_directory.mkdir(parents=True, exist_ok=True)
    with (state_directory / "rebuild.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return None
        with (state_directory / "rebuild.log").open("w") as log:
            worker = subprocess.Popen(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--worker",
                    "--state-directory",
                    str(state_directory),
                    "--configuration",
                    configuration,
                ],
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                cwd=state_directory,
                start_new_session=True,
                pass_fds=(lock.fileno(),),
            )
    return worker.pid


def main():
    parser = argparse.ArgumentParser(
        description="Run the machine rebuild detached from the steward session."
    )
    parser.add_argument("--state-directory", type=Path, required=True)
    parser.add_argument("--configuration", required=True)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    arguments = parser.parse_args()
    state_directory = arguments.state_directory.expanduser().resolve()
    if arguments.worker:
        return run_rebuild(state_directory, arguments.configuration)
    process_id = launch_rebuild(state_directory, arguments.configuration)
    print(
        json.dumps(
            {
                "status": "started" if process_id is not None else "already_running",
                "process_id": process_id,
                "state_directory": str(state_directory),
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
