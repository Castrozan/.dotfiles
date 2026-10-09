import os
import subprocess
from pathlib import Path


def test_home_manager_passes_its_acquired_descriptor_to_the_scope(
    managed_rebuild_environment, tmp_path
):
    rebuild_directory = Path(__file__).resolve().parents[2] / "scripts/rebuild"
    entrypoint = tmp_path / "rebuild"
    entrypoint.write_text(
        (rebuild_directory / "rebuild")
        .read_text()
        .replace(
            "@exclusiveRunLockHelper@",
            managed_rebuild_environment["EXCLUSIVE_RUN_LOCK_HELPER"],
        )
        .replace(
            "@exclusiveRunScopePython@",
            managed_rebuild_environment["EXCLUSIVE_RUN_SCOPE_PYTHON"],
        )
    )
    native = tmp_path / "home-manager"
    native.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$@"\nexit 42\n')
    native.chmod(0o755)
    program = f'''source "{entrypoint}"
detect_backend_name() {{ echo home-manager; }}
source "{rebuild_directory}/backends/home-manager"
prepare_exclusive_rebuild_lock
switch_with_the_installed_home_manager 'a b#host'
'''
    completed = subprocess.run(
        ["bash", "-c", program],
        env={**managed_rebuild_environment, "PATH": f"{tmp_path}:{os.environ['PATH']}"},
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert completed.returncode == 42, completed.stderr
    assert completed.stdout.splitlines() == [
        "switch",
        "--flake",
        "a b#host",
        "-b",
        "backup",
    ]
