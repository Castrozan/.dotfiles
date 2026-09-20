import os
import shutil
import subprocess
from pathlib import Path

ARTIFACT_DIRECTORY_NAMES = frozenset({".pytest_cache", ".ruff_cache", "__pycache__"})
PRUNED_DIRECTORY_NAMES = frozenset({".git", ".worktrees", "node_modules", "result"})
DOCKER_LEFTOVER_PRUNE_COMMANDS = (
    ("docker", "builder", "prune", "--force", "--filter", "until=24h"),
    ("docker", "image", "prune", "--force"),
)


def artifact_directories_under(root: Path) -> list[Path]:
    found = []
    for directory, subdirectories, _ in os.walk(root):
        unpruned = [
            name for name in subdirectories if name not in PRUNED_DIRECTORY_NAMES
        ]
        found.extend(
            Path(directory) / name
            for name in unpruned
            if name in ARTIFACT_DIRECTORY_NAMES
        )
        subdirectories[:] = [
            name for name in unpruned if name not in ARTIFACT_DIRECTORY_NAMES
        ]
    return found


def prune_docker_build_leftovers_the_run_did_not_reuse(log) -> None:
    if shutil.which("docker") is None:
        log.write("docker is not on PATH, so the run left no build cache to prune\n")
        return
    for command in DOCKER_LEFTOVER_PRUNE_COMMANDS:
        completed = subprocess.run(list(command), capture_output=True, text=True)
        outcome_lines = completed.stdout.strip().splitlines() or [
            completed.stderr.strip()
        ]
        log.write(
            f"{' '.join(command)}: exit {completed.returncode}, {outcome_lines[-1]}\n"
        )
