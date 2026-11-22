import dataclasses
import subprocess
from pathlib import Path

COMMAND_TIMEOUT_SECONDS = 900
GIT_TIMEOUT_SECONDS = 120
MISSING_PROGRAM_EXIT_CODE = 127
RENAMED_OR_COPIED = frozenset("RC")


@dataclasses.dataclass(frozen=True)
class CommandResult:
    exit_code: int
    output: str


def completed_result(completed: subprocess.CompletedProcess) -> CommandResult:
    return CommandResult(completed.returncode, completed.stdout + completed.stderr)


def run_program(root: Path, arguments: list[str]) -> CommandResult:
    try:
        completed = subprocess.run(
            arguments,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        return CommandResult(
            MISSING_PROGRAM_EXIT_CODE, f"{arguments[0]} is not on PATH"
        )
    return completed_result(completed)


def run_shell(root: Path, command: str) -> CommandResult:
    return run_program(root, ["bash", "-c", command])


def git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        check=False,
        timeout=GIT_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0:
        raise SystemExit(
            f"git {' '.join(arguments)} failed: {completed.stderr.strip()}"
        )
    return completed.stdout


def changed_paths(root: Path) -> list[str]:
    entries = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    fields = iter(entries.split("\0"))
    paths = []
    for field in fields:
        if not field:
            continue
        paths.append(field[3:])
        if RENAMED_OR_COPIED & set(field[:2]):
            next(fields, None)
    return paths


def untracked_paths(root: Path) -> set[str]:
    listed = git(root, "ls-files", "--others", "--exclude-standard", "-z")
    return {path for path in listed.split("\0") if path}


def untracked_diff(root: Path, path: str) -> str:
    return run_program(
        root, ["git", "diff", "--no-index", "--", "/dev/null", path]
    ).output


def change_diff(root: Path, base_revision: str) -> str:
    tracked = git(root, "diff", base_revision, "--")
    added = [untracked_diff(root, path) for path in sorted(untracked_paths(root))]
    return tracked + "".join(added)


def tail(text: str, line_count: int) -> str:
    return "\n".join(text.splitlines()[-line_count:])
