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


def repository_entry_counts(repository_root: Path) -> dict[str, int]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=repository_root,
        capture_output=True,
        check=True,
        timeout=5,
    )
    paths = [
        os.fsdecode(path)
        for path in result.stdout.split(b"\0")
        if path and os.path.lexists(repository_root / os.fsdecode(path))
    ]
    return directory_entry_counts(paths)


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
