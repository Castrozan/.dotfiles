"""Tests for git-history.py — script quality, cache behavior, and cross-repo portability."""

import hashlib
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "git-history.py"
REPO_ROOT = Path(
    subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        cwd=str(Path(__file__).resolve().parent),
    ).strip()
)


def run_gh(*args: str, repo: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    cmd = ["python3", str(SCRIPT)]
    if repo:
        cmd += ["--repo", repo]
    cmd += list(args)
    return subprocess.run(cmd, capture_output=True, text=True, check=check, cwd=str(REPO_ROOT))


def cache_path(root: Path, layer: int) -> Path:
    repo_hash = hashlib.md5(str(root).encode()).hexdigest()[:12]
    return Path(f"/tmp/gitlog-{root.name}-{repo_hash}-L{layer}.txt")


@pytest.fixture(autouse=True)
def clean_cache():
    """Clean cache before and after each test."""
    run_gh("clean", check=False)
    yield
    run_gh("clean", check=False)


# --- Script quality ---


def test_script_is_executable():
    assert os.access(SCRIPT, os.X_OK)


def test_script_has_shebang():
    with open(SCRIPT) as f:
        assert f.readline().startswith("#!/usr/bin/env python3")


def test_help_shows_usage():
    result = run_gh("dump", "--help")
    assert "layer" in result.stdout.lower()


def test_unknown_command_fails():
    result = run_gh("nonexistent", check=False)
    assert result.returncode != 0


# --- Layer 1: titles + file paths ---


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


def test_layer1_contains_commit_hashes():
    run_gh("dump")
    path = cache_path(REPO_ROOT, 1)
    lines = path.read_text(errors="replace").splitlines()
    commit_lines = [l for l in lines if len(l) >= 9 and l[8] == " " and all(c in "0123456789abcdef" for c in l[:8])]
    assert len(commit_lines) > 100


# --- Layer 2: full patches ---


def test_dump_layer2_creates_file():
    run_gh("dump", "--layer", "2")
    path = cache_path(REPO_ROOT, 2)
    assert path.exists()
    assert path.stat().st_size > path.parent.joinpath(cache_path(REPO_ROOT, 1).name).stat().st_size if cache_path(REPO_ROOT, 1).exists() else True


def test_layer2_has_header():
    run_gh("dump", "--layer", "2")
    path = cache_path(REPO_ROOT, 2)
    with open(path, "rb") as f:
        first_line = f.readline().decode(errors="replace")
    assert first_line.startswith("# HEAD: ")


def test_layer2_contains_diff_content():
    run_gh("dump", "--layer", "2")
    path = cache_path(REPO_ROOT, 2)
    content = path.read_bytes()[:50000].decode(errors="replace")
    assert "diff --git" in content or "+++" in content


# --- Layer 3: both layers ---


def test_dump_layer3_creates_both():
    run_gh("dump", "--layer", "3")
    assert cache_path(REPO_ROOT, 1).exists()
    assert cache_path(REPO_ROOT, 2).exists()


# --- Cache behavior ---


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
    assert "Layer 1:" in result.stdout
    assert "fresh" in result.stdout


def test_info_shows_not_dumped():
    result = run_gh("info")
    assert "not dumped" in result.stdout


def test_clean_removes_files():
    run_gh("dump", "--layer", "3")
    assert cache_path(REPO_ROOT, 1).exists()
    run_gh("clean")
    assert not cache_path(REPO_ROOT, 1).exists()
    assert not cache_path(REPO_ROOT, 2).exists()


# --- Path command ---


def test_path_returns_l1_by_default():
    result = run_gh("path")
    assert result.stdout.strip().endswith("-L1.txt")


def test_path_returns_l2():
    result = run_gh("path", "--layer", "2")
    assert result.stdout.strip().endswith("-L2.txt")


def test_path_is_consistent():
    result1 = run_gh("path")
    result2 = run_gh("path")
    assert result1.stdout == result2.stdout


# --- Cross-repo portability ---


def test_different_repos_get_different_paths():
    p1 = run_gh("path").stdout.strip()
    # Find another git repo on the system
    other_repos = [
        p
        for p in [Path.home() / "repo" / "openclaw-mesh", Path.home() / "repo" / "openclaw"]
        if p.exists() and (p / ".git").exists()
    ]
    if not other_repos:
        pytest.skip("no other git repos found for cross-repo test")
    p2 = run_gh("path", repo=str(other_repos[0])).stdout.strip()
    assert p1 != p2


# --- Not a git repo ---


def test_non_git_dir_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_gh("dump", repo=tmpdir, check=False)
        assert result.returncode != 0
        assert "not a git repo" in result.stderr


# --- Searchability: the actual use case ---


def test_grep_finds_known_commit_in_layer1():
    """Layer 1 dump should be searchable with grep and find known commits."""
    run_gh("dump")
    path = cache_path(REPO_ROOT, 1)
    result = subprocess.run(
        ["grep", "-i", "feat", str(path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert len(result.stdout.splitlines()) > 10


def test_grep_finds_file_paths_in_layer1():
    """File paths in layer 1 enable discovery by directory structure."""
    run_gh("dump")
    path = cache_path(REPO_ROOT, 1)
    result = subprocess.run(
        ["grep", "-c", ".nix", str(path)],
        capture_output=True,
        text=True,
    )
    assert int(result.stdout.strip()) > 50


def test_multi_keyword_grep_on_layer2():
    """Layer 2 enables searching actual code content across all history."""
    run_gh("dump", "--layer", "2")
    path = cache_path(REPO_ROOT, 2)
    result = subprocess.run(
        ["grep", "-ci", "import", str(path)],
        capture_output=True,
        text=True,
    )
    assert int(result.stdout.strip()) > 10
