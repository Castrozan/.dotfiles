import hashlib
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
    return {
        1: Path(f"/tmp/gitlog-{name}-{repo_hash}-L1.txt"),
        2: Path(f"/tmp/gitlog-{name}-{repo_hash}-L2.txt"),
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
