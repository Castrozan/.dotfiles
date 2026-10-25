import os
import re
import subprocess
from pathlib import Path

from cycle_commands import TIMED_OUT_RETURN_CODE, CommandRunner
from cycle_configuration import CycleConfiguration
from cycle_records import (
    current_timestamp,
    revision_log_path,
    revision_record_path,
    write_record,
)
from cycle_repository import Repository

VALIDATION_TIMEOUT_SECONDS = 3 * 60 * 60
TRANSIENT_FAILURE_PATTERN = re.compile(
    r"interrupted by (the user|signal)|received signal|HTTP error (403|429|50[0-9])|unable to download"
    r"|couldn't resolve host|connection (timed out|refused)|no space left on device",
    re.IGNORECASE,
)


def build_command(
    configuration: CycleConfiguration, revision: str, entrypoint_revision: str
) -> list[str]:
    return [
        configuration.nix_binary,
        "--extra-experimental-features",
        "nix-command flakes",
        "build",
        "--no-link",
        "--print-out-paths",
        "--no-write-lock-file",
        "--override-input",
        "dotfiles",
        configuration.pinned_repository_reference(revision),
        configuration.entrypoint_installable(entrypoint_revision),
    ]


def run_build(arguments: list[str], directory: Path, log_path: Path) -> tuple[int, str]:
    with log_path.open("w") as log:
        try:
            completed = subprocess.run(
                arguments,
                cwd=directory,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=log,
                text=True,
                timeout=VALIDATION_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return TIMED_OUT_RETURN_CODE, ""
    return completed.returncode, completed.stdout


def built_toplevel(standard_output: str) -> str:
    store_paths = [
        line.strip()
        for line in standard_output.splitlines()
        if line.strip().startswith("/nix/store/")
    ]
    return store_paths[-1] if store_paths else ""


def verdict_for(return_code: int, toplevel: str, log_text: str) -> str:
    if return_code == 0 and toplevel:
        return "green"
    if return_code == TIMED_OUT_RETURN_CODE or TRANSIENT_FAILURE_PATTERN.search(
        log_text
    ):
        return "transient"
    return "red"


def validate_revision(
    configuration: CycleConfiguration,
    runner: CommandRunner,
    revision: str,
    attempt: int,
    build=run_build,
) -> dict:
    configuration.validations_directory.mkdir(parents=True, exist_ok=True)
    os.chdir(configuration.state_directory)
    log_path = revision_log_path(configuration.validations_directory, revision)
    started = current_timestamp()
    entrypoint_head = Repository(configuration.entrypoint, runner).revision("HEAD")
    return_code, standard_output = build(
        build_command(configuration, revision, entrypoint_head),
        configuration.state_directory,
        log_path,
    )
    toplevel = built_toplevel(standard_output)
    record = {
        "revision": revision,
        "attempt": attempt,
        "status": verdict_for(
            return_code, toplevel, log_path.read_text(errors="replace")
        ),
        "return_code": return_code,
        "toplevel": toplevel,
        "entrypoint_head": entrypoint_head,
        "started": started,
        "finished": current_timestamp(),
        "log": str(log_path),
    }
    write_record(
        revision_record_path(configuration.validations_directory, revision), record
    )
    if record["status"] == "green":
        configuration.last_green_file.write_text(revision + "\n")
    return record
