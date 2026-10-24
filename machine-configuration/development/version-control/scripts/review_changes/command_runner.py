import subprocess
from pathlib import Path


class ReviewTargetError(Exception):
    pass


def run_command(
    arguments: list[str], working_directory: Path | None = None
) -> subprocess.CompletedProcess:
    return subprocess.run(
        arguments,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        cwd=working_directory,
    )


def run_git(arguments: list[str], working_directory: Path | None = None) -> str:
    result = run_command(["git", *arguments], working_directory)
    if result.returncode != 0:
        raise ReviewTargetError(
            result.stderr.strip() or f"git {' '.join(arguments)} failed"
        )
    return result.stdout.strip()
