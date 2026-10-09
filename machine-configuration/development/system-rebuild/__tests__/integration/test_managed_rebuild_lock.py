import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


def wait_for_path(path):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if path.exists():
            return
        time.sleep(0.01)
    raise TimeoutError(str(path))


def stop_holder(holder):
    holder.terminate()
    try:
        holder.wait(timeout=5)
    finally:
        if holder.poll() is None:
            holder.kill()
            holder.wait(timeout=5)


def start_holder(environment, tmp_path):
    acquired = tmp_path / "acquired"
    holder = subprocess.Popen(
        [
            environment["SYSTEM_REBUILD_LOCK_GUARD"],
            "bash",
            "-c",
            f'touch "{acquired}"; sleep 30',
        ],
        env=environment,
        start_new_session=True,
    )
    wait_for_path(acquired)
    return holder


@pytest.mark.parametrize("platform", ["nixos", "darwin"])
def test_managed_entrypoints_share_contention_and_diagnostic_passthrough(
    managed_rebuild_environment, tmp_path, platform
):
    environment = managed_rebuild_environment
    native = tmp_path / "native"
    native.write_text('printf "NATIVE_COMMAND %s\\n" "$*"\n')
    native.chmod(0o755)
    native.write_text("#!/usr/bin/env bash\n" + native.read_text())
    environment.update(
        REAL_NIXOS_REBUILD=str(native),
        REAL_DARWIN_REBUILD=str(native),
        DOTFILES_REBUILD_WRAPPER="1",
    )
    holder = start_holder(environment, tmp_path)
    try:
        completed = subprocess.run(
            ["bash", str(SCRIPTS / f"{platform}-rebuild-guard"), "build"],
            env=environment,
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert completed.returncode == 99, completed.stderr
        assert "NATIVE_COMMAND" not in completed.stdout
        for diagnostic in ("--help", "--version"):
            completed = subprocess.run(
                ["bash", str(SCRIPTS / f"{platform}-rebuild-guard"), diagnostic],
                env=environment,
                capture_output=True,
                text=True,
                timeout=5,
            )
            assert completed.returncode == 0, completed.stderr
            assert diagnostic in completed.stdout
    finally:
        stop_holder(holder)


def test_privilege_handoff_closes_outer_descriptors_before_guard_acquisition(
    managed_rebuild_environment, tmp_path
):
    started = tmp_path / "privileged-started"
    handoff = tmp_path / "privilege_handoff.py"
    handoff.write_text(
        "import os\nimport sys\n"
        "os.closerange(3, 256)\n"
        "os.execv(sys.argv[1], sys.argv[1:])\n"
    )
    outer_descriptor = os.open(tmp_path / "outer-descriptor", os.O_CREAT | os.O_RDWR)
    holder = subprocess.Popen(
        [
            sys.executable,
            str(handoff),
            managed_rebuild_environment["SYSTEM_REBUILD_LOCK_GUARD"],
            "bash",
            "-c",
            f'touch "{started}"; sleep 30',
        ],
        env=managed_rebuild_environment,
        pass_fds=(outer_descriptor,),
        start_new_session=True,
    )
    os.close(outer_descriptor)
    try:
        wait_for_path(started)
        completed = subprocess.run(
            [managed_rebuild_environment["SYSTEM_REBUILD_LOCK_GUARD"], "true"],
            env=managed_rebuild_environment,
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert completed.returncode == 99, completed.stderr
    finally:
        stop_holder(holder)


def test_darwin_native_driver_keeps_entrypoint_and_arguments(
    managed_rebuild_environment, tmp_path
):
    native = tmp_path / "native"
    native.write_text('printf "%s\\n" "$0"; printf "%s\\n" "$@"\n')
    managed_rebuild_environment["REAL_DARWIN_REBUILD"] = str(native)
    completed = subprocess.run(
        [
            "bash",
            str(SCRIPTS / "darwin-rebuild-guard"),
            "activate",
            "--flake",
            "a b#host",
        ],
        env=managed_rebuild_environment,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.splitlines() == [
        "/run/current-system/sw/bin/darwin-rebuild",
        "activate",
        "--flake",
        "a b#host",
    ]


def test_missing_helper_cannot_start_native_workload(
    managed_rebuild_environment, tmp_path
):
    managed_rebuild_environment["EXCLUSIVE_RUN_LOCK_HELPER"] = str(tmp_path / "absent")
    completed = subprocess.run(
        [managed_rebuild_environment["SYSTEM_REBUILD_LOCK_GUARD"], "echo", "UNGUARDED"],
        env=managed_rebuild_environment,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert completed.returncode == 1
    assert "UNGUARDED" not in completed.stdout
    assert "lock helper is missing" in completed.stderr
