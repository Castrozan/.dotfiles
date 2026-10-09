import os
import shutil
import sys
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[5]


@pytest.fixture
def managed_rebuild_environment(tmp_path):
    helper_source = REPOSITORY_ROOT / "agent-harness/session-control"
    for name in (
        "exclusive-run-lock.sh",
        "exclusive_run_lock.py",
        "exclusive_run_scope.py",
    ):
        shutil.copyfile(helper_source / name, tmp_path / name)
    helper = tmp_path / "exclusive-run-lock.sh"
    helper.write_text(
        helper.read_text().replace('"/tmp/dotfiles-', f'"{tmp_path}/dotfiles-')
    )
    return {
        **os.environ,
        "EXCLUSIVE_RUN_LOCK_HELPER": str(helper),
        "EXCLUSIVE_RUN_SCOPE_PYTHON": sys.executable,
        "SYSTEM_REBUILD_LOCK_GUARD": str(
            REPOSITORY_ROOT
            / "machine-configuration/development/system-rebuild/scripts/system-rebuild-lock"
        ),
        "DARWIN_REBUILD_SHELL": shutil.which("bash"),
        "DARWIN_REBUILD_ENTRYPOINT": "/run/current-system/sw/bin/darwin-rebuild",
    }
