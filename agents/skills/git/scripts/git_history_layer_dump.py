import subprocess
import sys
import time
from pathlib import Path

from git_history_cache_file_inspection import (
    file_size_human,
    is_stale,
    line_count,
)
from git_history_repo_and_cache_paths import current_head


def dump_layer(root: Path, layer: int, paths: dict[int, Path], force: bool) -> None:
    path = paths[layer]
    head = current_head(root)

    if not force and not is_stale(path, head):
        lines = line_count(path)
        print(f"{path} ({lines} lines, fresh)", file=sys.stderr)
        return

    git_base = ["git", "-C", str(root)]

    if layer == 1:
        print("Dumping layer 1: titles + file paths...", file=sys.stderr)
        git_cmd = git_base + [
            "log",
            "--all",
            "--format=%h %s%n%b",
            "--name-only",
        ]
        layer_desc = "1 (titles + file paths)"
    else:
        print("Dumping layer 2: full patches...", file=sys.stderr)
        git_cmd = git_base + ["log", "--all", "-p", "--format=%h %s"]
        layer_desc = "2 (full patches)"

    header = (
        f"# HEAD: {head}\n"
        f"# Repo: {root}\n"
        f"# Layer: {layer_desc}\n"
        f"# Generated: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}\n\n"
    )
    result = subprocess.run(git_cmd, capture_output=True)
    if result.returncode != 0:
        print(
            f"error: git log failed with exit code {result.returncode}",
            file=sys.stderr,
        )
        sys.exit(1)
    with open(path, "wb") as f:
        f.write(header.encode())
        f.write(result.stdout)

    lines = line_count(path)
    size = file_size_human(path)
    print(f"{path} ({lines} lines, {size})", file=sys.stderr)
