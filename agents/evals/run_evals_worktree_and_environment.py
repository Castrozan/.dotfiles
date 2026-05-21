import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

EVAL_WORKING_DIRECTORY: Path = REPO_ROOT


@contextmanager
def temporary_eval_worktree():
    global EVAL_WORKING_DIRECTORY
    worktree_path = Path(tempfile.mkdtemp(prefix="eval-worktree-"))
    try:
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(worktree_path)],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
        )
        EVAL_WORKING_DIRECTORY = worktree_path
        yield worktree_path
    finally:
        EVAL_WORKING_DIRECTORY = REPO_ROOT
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree_path)],
            cwd=REPO_ROOT,
            capture_output=True,
        )
        if worktree_path.exists():
            shutil.rmtree(worktree_path, ignore_errors=True)


def build_filtered_environment() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
