from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path


def git_root(repo: str | None = None) -> Path:
    cmd = ["git", "rev-parse", "--show-toplevel"]
    if repo:
        cmd = ["git", "-C", repo, "rev-parse", "--show-toplevel"]
    try:
        return Path(
            subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
        )
    except subprocess.CalledProcessError:
        target = repo or "current directory"
        print(f"error: not a git repo: {target}", file=sys.stderr)
        sys.exit(1)


def cache_paths(root: Path) -> dict[int, Path]:
    repo_hash = hashlib.md5(str(root).encode()).hexdigest()[:12]
    name = root.name
    cache_directory = (
        Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "git-history"
    )
    cache_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    return {
        1: cache_directory / f"gitlog-{name}-{repo_hash}-L1.txt",
        2: cache_directory / f"gitlog-{name}-{repo_hash}-L2.txt",
    }


def current_head(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        return "unknown"
