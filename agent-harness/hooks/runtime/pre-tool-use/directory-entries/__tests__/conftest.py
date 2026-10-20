import subprocess
import sys
from pathlib import Path

import pytest

POLICY_DIRECTORY = Path(__file__).resolve().parents[1]
HOOKS_DIRECTORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(POLICY_DIRECTORY))
sys.path.insert(0, str(HOOKS_DIRECTORY / "common"))


@pytest.fixture
def repository_at_entry_limit(tmp_path):
    repository_root = tmp_path / "repository"
    repository_root.mkdir()
    subprocess.run(["git", "init", "--quiet", str(repository_root)], check=True)
    source = repository_root / "source"
    source.mkdir()
    for index in range(15):
        (source / f"file{index}.py").touch()
    return repository_root
