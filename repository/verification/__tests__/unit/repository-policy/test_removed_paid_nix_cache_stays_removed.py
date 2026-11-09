from pathlib import Path
import subprocess

REPOSITORY = Path(__file__).resolve().parents[5]
REMOVED_CACHE_FILES = (
    ".github/workflows/nix-binary-cache.yml",
    "machine-configuration/development/system-rebuild/dotfiles-binary-cache.json",
    "machine-configuration/development/system-rebuild/dotfiles-binary-cache-system.nix",
)
REMOVED_CACHE_MARKERS = (
    b"dotfiles-usage-snapshots/nix-cache",
    b"dotfiles-chise-1:",
)
ACTIVE_CONFIGURATION_SUFFIXES = (
    ".nix",
    ".json",
    ".yml",
    ".yaml",
    ".sh",
    ".py",
    ".toml",
)


def tracked_active_configuration_files():
    tracked = subprocess.check_output(
        ["git", "ls-files"], cwd=REPOSITORY, text=True
    ).splitlines()
    own_file = Path(__file__).resolve()
    candidates = (REPOSITORY / relative for relative in tracked)
    return [
        candidate
        for candidate in candidates
        if candidate.suffix in ACTIVE_CONFIGURATION_SUFFIXES
        and candidate.is_file()
        and candidate.resolve() != own_file
    ]


def test_the_paid_nix_cache_files_stay_removed():
    assert [
        relative for relative in REMOVED_CACHE_FILES if (REPOSITORY / relative).exists()
    ] == []


def test_no_active_configuration_points_at_the_paid_nix_cache():
    references = [
        str(path.relative_to(REPOSITORY))
        for path in tracked_active_configuration_files()
        if any(marker in path.read_bytes() for marker in REMOVED_CACHE_MARKERS)
    ]
    assert references == []
