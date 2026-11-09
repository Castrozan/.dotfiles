import subprocess
from pathlib import Path

GIT_TIMEOUT_SECONDS = 30


def resolve_repository_root(requested_root: str) -> Path:
    if requested_root:
        requested_directory = Path(requested_root).expanduser().resolve()
        if not requested_directory.is_dir():
            raise SystemExit(f"--root {requested_root} is not a directory")
        return requested_directory
    checkout_toplevel = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
        timeout=GIT_TIMEOUT_SECONDS,
    )
    if checkout_toplevel.returncode != 0:
        raise SystemExit(
            "the current directory belongs to no git checkout: "
            "pass --root <absolute checkout path>"
        )
    return Path(checkout_toplevel.stdout.strip())


def is_inside_git_checkout(directory: Path) -> bool:
    return (
        subprocess.run(
            ["git", "-C", str(directory), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        ).returncode
        == 0
    )


def workspace_arguments(
    working_directory: Path, inside_git_checkout: bool
) -> list[str]:
    if inside_git_checkout:
        return ["--cwd", str(working_directory)]
    return ["--folder"]
