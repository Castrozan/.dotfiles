from pathlib import Path

from cycle_commands import CommandRunner
from cycle_configuration import CycleConfiguration
from cycle_records import revision_log_path

VALIDATION_SCOPE_PREFIX = "steward-validate-"
ACTIVATION_SCOPE_PREFIX = "steward-activation-"
SCOPE_QUERY_TIMEOUT_SECONDS = 15
REBUILD_EXECUTABLE_SUFFIX = b"-rebuild/bin/rebuild"
PROCESS_DIRECTORY = Path("/proc")


class JobStateUnknown(RuntimeError):
    pass


def scope_unit(prefix: str, revision: str) -> str:
    return f"{prefix}{revision[:8]}"


def active_job_scopes(runner: CommandRunner, directory: Path) -> tuple[str, ...]:
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
            "steward-activation*",
        ],
        directory,
        SCOPE_QUERY_TIMEOUT_SECONDS,
    )
    if not result.succeeded:
        raise JobStateUnknown(f"cannot list steward job scopes: {result.explanation}")
    return tuple(line.split()[0] for line in result.output.splitlines() if line.strip())


def scope_command(prefix: str, revision: str, command: list[str]) -> list[str]:
    return [
        "systemd-run",
        "--user",
        "--scope",
        "--quiet",
        "--collect",
        f"--unit={scope_unit(prefix, revision)}",
        "--",
        *command,
    ]


def launch_validation(
    configuration: CycleConfiguration,
    runner: CommandRunner,
    revision: str,
    attempt: int,
    cycle_command: list[str],
) -> None:
    worker = [
        *cycle_command,
        "validate-revision",
        "--revision",
        revision,
        "--attempt",
        str(attempt),
    ]
    runner.launch_detached(
        scope_command(VALIDATION_SCOPE_PREFIX, revision, worker),
        configuration.state_directory,
        configuration.validations_directory / f"{revision}.outer.log",
    )


def launch_activation(
    configuration: CycleConfiguration, runner: CommandRunner, revision: str
) -> Path:
    log_path = revision_log_path(configuration.activations_directory, revision)
    rebuild = [
        configuration.rebuild_command,
        "--override-input",
        "dotfiles",
        configuration.pinned_repository_reference(revision),
    ]
    runner.launch_detached(
        scope_command(ACTIVATION_SCOPE_PREFIX, revision, rebuild),
        configuration.state_directory,
        log_path,
    )
    return log_path


def rebuild_running(process_directory: Path = PROCESS_DIRECTORY) -> bool:
    for command_line in process_directory.glob("[0-9]*/cmdline"):
        try:
            arguments = command_line.read_bytes().split(b"\0")
        except OSError:
            continue
        if any(
            argument.endswith(REBUILD_EXECUTABLE_SUFFIX) for argument in arguments[:2]
        ):
            return True
    return False
