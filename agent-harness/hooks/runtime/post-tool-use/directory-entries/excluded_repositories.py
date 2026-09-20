import fnmatch
import os
import subprocess
from pathlib import Path

DEFAULT_EXCLUDED_REPOSITORIES_FILE = (
    Path.home()
    / ".dotfiles"
    / "private-configuration"
    / "agent-harness"
    / "directory-entry-guard"
    / "excluded-repositories.txt"
)


def resolve_excluded_repositories_file() -> Path:
    override = os.environ.get("DIRECTORY_ENTRY_EXCLUDED_REPOSITORIES_FILE")
    if override:
        return Path(override)
    return DEFAULT_EXCLUDED_REPOSITORIES_FILE


def load_excluded_repository_patterns() -> list[str]:
    patterns_file = resolve_excluded_repositories_file()
    try:
        raw_lines = patterns_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    return [
        os.path.expanduser(stripped)
        for stripped in (line.strip() for line in raw_lines)
        if stripped and not stripped.startswith("#")
    ]


def origin_remote_url(repository_root: Path) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(repository_root), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    url = result.stdout.strip()
    return url if result.returncode == 0 and url else None


def repository_is_excluded(repository_root: Path, patterns: list[str]) -> bool:
    if not patterns:
        return False
    candidates = {str(repository_root), str(Path(repository_root).resolve())}
    remote_url = origin_remote_url(repository_root)
    if remote_url:
        candidates.add(remote_url)
    return any(
        fnmatch.fnmatch(candidate, pattern)
        for candidate in candidates
        for pattern in patterns
    )
