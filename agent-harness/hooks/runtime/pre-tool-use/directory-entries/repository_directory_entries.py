import json
import os
import subprocess
from pathlib import Path

from directory_entry_policy import DIRECTORY_ENTRY_LIMIT, directory_entry_counts

BASELINE_RELATIVE_PATH = Path(
    "repository/verification/quality/directory-entries/baseline.json"
)


def repository_root_for_path(path: Path) -> Path | None:
    directory = path.parent
    while not directory.is_dir() and directory != directory.parent:
        directory = directory.parent
    result = subprocess.run(
        ["git", "-C", str(directory), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    return Path(result.stdout.strip()) if result.returncode == 0 else None


def repository_entry_paths(repository_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=repository_root,
        capture_output=True,
        check=True,
        timeout=5,
    )
    return [
        os.fsdecode(path)
        for path in result.stdout.split(b"\0")
        if path and os.path.lexists(repository_root / os.fsdecode(path))
    ]


def paths_not_ignored_by_git(repository_root: Path, relative_paths) -> set[str]:
    result = subprocess.run(
        ["git", "check-ignore", "--stdin", "-z"],
        cwd=repository_root,
        input=b"\0".join(os.fsencode(path) for path in relative_paths),
        capture_output=True,
        timeout=5,
    )
    if result.returncode not in (0, 1):
        raise subprocess.CalledProcessError(
            result.returncode, result.args, result.stdout, result.stderr
        )
    ignored_paths = {os.fsdecode(path) for path in result.stdout.split(b"\0") if path}
    return set(relative_paths) - ignored_paths


def repository_entry_counts(repository_root: Path) -> dict[str, int]:
    return directory_entry_counts(repository_entry_paths(repository_root))


def directory_entry_ceilings(repository_root: Path) -> dict[str, int]:
    baseline = repository_root / BASELINE_RELATIVE_PATH
    if not baseline.exists():
        return {}
    ceilings = json.loads(baseline.read_text())
    if not isinstance(ceilings, dict) or _has_invalid_directory_ceilings(ceilings):
        raise ValueError(f"Invalid directory entry baseline: {baseline}")
    return ceilings


def _has_invalid_directory_ceilings(ceilings: dict) -> bool:
    return any(
        not isinstance(directory, str)
        or type(count) is not int
        or count <= DIRECTORY_ENTRY_LIMIT
        for directory, count in ceilings.items()
    )
