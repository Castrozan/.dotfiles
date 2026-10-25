import fcntl
import os
import subprocess
from pathlib import Path

from cycle_commands import CommandRunner
from cycle_configuration import SYSTEMD_SCOPE_ISOLATION, CycleConfiguration
from cycle_records import revision_log_path

VALIDATION_SCOPE_PREFIX = "steward-validate-"
ACTIVATION_SCOPE_PREFIX = "steward-activation-"
QUERY_TIMEOUT_SECONDS = 15
REBUILD_EXECUTABLE_SUFFIX = "-rebuild/bin/rebuild"
DARWIN_BACKGROUND_PRIORITY = ["taskpolicy", "-b"]


class JobStateUnknown(RuntimeError):
    pass


def job_name(prefix: str, revision: str) -> str:
    return f"{prefix}{revision[:8]}"


def active_systemd_scopes(runner: CommandRunner, directory: Path) -> tuple[str, ...]:
    result = runner.run(
        [
            "systemctl",
            "--user",
            "list-units",
            "--type=scope",
            "--state=active",
            "--no-legend",
            "--plain",
            f"{VALIDATION_SCOPE_PREFIX}*",
            f"{ACTIVATION_SCOPE_PREFIX}*",
        ],
        directory,
        QUERY_TIMEOUT_SECONDS,
    )
    if not result.succeeded:
        raise JobStateUnknown(f"cannot list steward job scopes: {result.explanation}")
    return tuple(line.split()[0] for line in result.output.splitlines() if line.strip())


def job_holds_its_lock(lock_path: Path) -> bool:
    try:
        descriptor = os.open(lock_path, os.O_RDONLY)
    except FileNotFoundError:
        return False
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return True
    finally:
        os.close(descriptor)
    return False


def active_detached_jobs(jobs_directory: Path) -> tuple[str, ...]:
    return tuple(
        lock.stem
        for lock in sorted(jobs_directory.glob("*.lock"))
        if job_holds_its_lock(lock)
    )


def active_jobs(
    configuration: CycleConfiguration, runner: CommandRunner
) -> tuple[str, ...]:
    if configuration.job_isolation == SYSTEMD_SCOPE_ISOLATION:
        return active_systemd_scopes(runner, configuration.state_directory)
    return active_detached_jobs(configuration.jobs_directory)


def run_job(lock_path: Path, command: list[str]) -> int:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            return subprocess.run(
                command, stdin=subprocess.DEVNULL, check=False
            ).returncode
        finally:
            lock_path.unlink(missing_ok=True)


def isolated_command(
    configuration: CycleConfiguration,
    name: str,
    command: list[str],
    cycle_command: list[str],
) -> list[str]:
    if configuration.job_isolation == SYSTEMD_SCOPE_ISOLATION:
        return [
            "systemd-run",
            "--user",
            "--scope",
            "--quiet",
            "--collect",
            f"--unit={name}",
            "--",
            *command,
        ]
    lock_path = configuration.jobs_directory / f"{name}.lock"
    return [*cycle_command, "run-job", "--lock", str(lock_path), "--", *command]


def validation_command(
    configuration: CycleConfiguration,
    revision: str,
    attempt: int,
    cycle_command: list[str],
) -> list[str]:
    worker = [
        *cycle_command,
        "validate-revision",
        "--revision",
        revision,
        "--attempt",
        str(attempt),
    ]
    if configuration.job_isolation != SYSTEMD_SCOPE_ISOLATION:
        worker = [*DARWIN_BACKGROUND_PRIORITY, *worker]
    name = job_name(VALIDATION_SCOPE_PREFIX, revision)
    return isolated_command(configuration, name, worker, cycle_command)


def activation_command(
    configuration: CycleConfiguration, revision: str, cycle_command: list[str]
) -> list[str]:
    rebuild = [configuration.rebuild_command]
    if configuration.entrypoint is not None:
        pinned = configuration.pinned_repository_reference(revision)
        rebuild = [*rebuild, "--override-input", "dotfiles", pinned]
    name = job_name(ACTIVATION_SCOPE_PREFIX, revision)
    return isolated_command(configuration, name, rebuild, cycle_command)


def launch_validation(
    configuration: CycleConfiguration,
    runner: CommandRunner,
    revision: str,
    attempt: int,
    cycle_command: list[str],
) -> None:
    runner.launch_detached(
        validation_command(configuration, revision, attempt, cycle_command),
        configuration.state_directory,
        configuration.validations_directory / f"{revision}.outer.log",
    )


def launch_activation(
    configuration: CycleConfiguration,
    runner: CommandRunner,
    revision: str,
    cycle_command: list[str],
) -> None:
    runner.launch_detached(
        activation_command(configuration, revision, cycle_command),
        configuration.state_directory,
        revision_log_path(configuration.activations_directory, revision),
    )


def is_rebuild_executable(argument: str) -> bool:
    return argument.endswith("/rebuild") and os.path.realpath(argument).endswith(
        REBUILD_EXECUTABLE_SUFFIX
    )


def rebuild_running(runner: CommandRunner, directory: Path) -> bool:
    result = runner.run(
        ["ps", "-A", "-ww", "-o", "args="], directory, QUERY_TIMEOUT_SECONDS
    )
    if not result.succeeded:
        raise JobStateUnknown(f"cannot list processes: {result.explanation}")
    return any(
        is_rebuild_executable(argument)
        for line in result.output.splitlines()
        for argument in line.split()[:2]
    )
