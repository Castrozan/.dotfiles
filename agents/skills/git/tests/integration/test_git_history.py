import hashlib
import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent.parent / "scripts" / "git-history.py"
REPO_ROOT = Path(
    subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        cwd=str(Path(__file__).resolve().parent),
    ).strip()
)


def run_gh(
    *args: str, repo: str | None = None, check: bool = True
) -> subprocess.CompletedProcess:
    cmd = ["python3", str(SCRIPT)]
    if repo:
        cmd += ["--repo", repo]
    cmd += list(args)
    return subprocess.run(
        cmd, capture_output=True, text=True, check=check, cwd=str(REPO_ROOT)
    )


def cache_path(root: Path, layer: int) -> Path:
    repo_hash = hashlib.md5(str(root).encode()).hexdigest()[:12]
    return Path(f"/tmp/gitlog-{root.name}-{repo_hash}-L{layer}.txt")


@pytest.fixture(autouse=True)
def clean_cache():
    for layer in (1, 2):
        path = cache_path(REPO_ROOT, layer)
        path.unlink(missing_ok=True)
    yield
    for layer in (1, 2):
        path = cache_path(REPO_ROOT, layer)
        path.unlink(missing_ok=True)


def test_script_has_shebang():
    with open(SCRIPT) as f:
        assert f.readline().startswith("#!/usr/bin/env python3")


def test_help_shows_usage():
    result = run_gh("dump", "--help")
    assert "layer" in result.stdout.lower()


def test_unknown_command_fails():
    result = run_gh("nonexistent", check=False)
    assert result.returncode != 0


def test_dump_layer1_creates_file():
    run_gh("dump")
    path = cache_path(REPO_ROOT, 1)
    assert path.exists()
    assert path.stat().st_size > 0


def test_layer1_has_header():
    run_gh("dump")
    path = cache_path(REPO_ROOT, 1)
    content = path.read_text(errors="replace")
    assert content.startswith("# HEAD: ")
    assert "# Repo:" in content
    assert "# Layer: 1" in content


def test_layer1_contains_file_paths():
    run_gh("dump")
    path = cache_path(REPO_ROOT, 1)
    content = path.read_text(errors="replace")
    assert ".nix" in content


def test_dump_layer2_creates_file():
    run_gh("dump", "--layer", "2")
    path = cache_path(REPO_ROOT, 2)
    assert path.exists()
    assert path.stat().st_size > 0


def test_dump_layer3_creates_both():
    run_gh("dump", "--layer", "3")
    assert cache_path(REPO_ROOT, 1).exists()
    assert cache_path(REPO_ROOT, 2).exists()


def test_cache_fresh_skips_redump():
    run_gh("dump")
    result = run_gh("dump")
    assert "fresh" in result.stderr


def test_force_redumps():
    run_gh("dump")
    result = run_gh("dump", "--force")
    assert "Dumping layer 1" in result.stderr


def test_info_shows_status():
    run_gh("dump")
    result = run_gh("info")
    assert "Repo:" in result.stdout
    assert "HEAD:" in result.stdout
    assert "fresh" in result.stdout


def test_clean_removes_files():
    run_gh("dump", "--layer", "3")
    assert cache_path(REPO_ROOT, 1).exists()
    run_gh("clean")
    assert not cache_path(REPO_ROOT, 1).exists()
    assert not cache_path(REPO_ROOT, 2).exists()


def test_path_returns_l1_by_default():
    result = run_gh("path")
    assert result.stdout.strip().endswith("-L1.txt")


def test_path_returns_l2():
    result = run_gh("path", "--layer", "2")
    assert result.stdout.strip().endswith("-L2.txt")


def test_non_git_dir_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_gh("dump", repo=tmpdir, check=False)
        assert result.returncode != 0
        assert "not a git repo" in result.stderr


def test_grep_finds_known_commit_in_layer1():
    run_gh("dump")
    path = cache_path(REPO_ROOT, 1)
    result = subprocess.run(
        ["grep", "-i", "feat", str(path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert len(result.stdout.splitlines()) > 10
