import os
import signal
import subprocess
import sys

import pytest

from staged_rebuild_support import SCRIPTS, read_events
from test_managed_rebuild_lock import start_holder, stop_holder, wait_for_path
from test_staged_sources import prefetch_environment


def prefetch_command(directory, name):
    preparation = directory / name
    preparation.mkdir()
    return [
        "bash",
        str(SCRIPTS / "prefetch-rebuild"),
        str(preparation / "request.json"),
        str(directory / "dotfiles"),
        "boot",
        "--flake",
        f"git+file://{directory}/private#chise",
    ]


def start_archive(environment, directory):
    log = (directory / "prefetch-output").open("w")
    holder = subprocess.Popen(
        prefetch_command(directory, "first"),
        env={**environment, "TEST_ARCHIVE_HOLD": "1"},
        stdout=log,
        stderr=log,
        start_new_session=True,
    )
    wait_for_path(directory / "archive-descendant-started")
    return holder, log


def stop_archive(holder, directory, process_group):
    (directory / "release-descendant").touch()
    if holder.poll() is None:
        holder.terminate()
    try:
        holder.wait(timeout=5)
    finally:
        try:
            os.killpg(process_group, signal.SIGKILL)
        except ProcessLookupError:
            pass


def test_archive_prefetch_contends_before_any_second_nix_client(
    managed_rebuild_environment, tmp_path
):
    environment = prefetch_environment(managed_rebuild_environment, tmp_path)
    holder, log = start_archive(environment, tmp_path)
    process_group = os.getpgid(int((tmp_path / "archive-pid").read_text()))
    try:
        contender = subprocess.run(
            prefetch_command(tmp_path, "second"),
            env=environment,
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert contender.returncode == 99, contender.stderr
        assert "LOCKED_BY_CONCURRENT_RUN" in contender.stderr
        assert len(read_events(tmp_path)) == 1
    finally:
        stop_archive(holder, tmp_path, process_group)
        log.close()


@pytest.mark.parametrize("target", ["archive", "prefetch"])
@pytest.mark.parametrize("termination_signal", [signal.SIGTERM, signal.SIGKILL])
def test_prefetch_death_keeps_machine_lock_while_archive_descendant_lives(
    managed_rebuild_environment, tmp_path, target, termination_signal
):
    environment = prefetch_environment(managed_rebuild_environment, tmp_path)
    holder, log = start_archive(environment, tmp_path)
    archive = int((tmp_path / "archive-pid").read_text())
    process_group = os.getpgid(archive)
    try:
        os.kill(archive if target == "archive" else process_group, termination_signal)
        contender = subprocess.run(
            [environment["SYSTEM_REBUILD_LOCK_GUARD"], "true"],
            env=environment,
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert contender.returncode == 99, contender.stderr
        (tmp_path / "release-descendant").touch()
        assert holder.wait(timeout=5) == 128 + termination_signal
        contender = subprocess.run(
            [environment["SYSTEM_REBUILD_LOCK_GUARD"], "true"],
            env=environment,
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert contender.returncode == 0, contender.stderr
        assert not (tmp_path / "first/request.json").exists()
    finally:
        stop_archive(holder, tmp_path, process_group)
        log.close()


@pytest.mark.parametrize("contended", [False, True])
def test_prefetch_releases_before_privilege_handoff_and_reacquires_fail_closed(
    managed_rebuild_environment, tmp_path, contended
):
    environment = prefetch_environment(managed_rebuild_environment, tmp_path)
    prepared = subprocess.run(
        prefetch_command(tmp_path, "prepared"),
        env=environment,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert prepared.returncode == 0, prepared.stderr
    assert (tmp_path / "prepared/sources").is_symlink()
    command_count = len(read_events(tmp_path))
    handoff = tmp_path / "handoff.py"
    handoff.write_text(
        "import os\nimport sys\nos.closerange(3, 256)\nos.execv(sys.argv[1], sys.argv[1:])\n"
    )
    environment.update(
        REAL_NIXOS_REBUILD=str(SCRIPTS / "staged-rebuild"),
        DOTFILES_REBUILD_WRAPPER="1",
    )
    holder = start_holder(environment, tmp_path) if contended else None
    try:
        activated = subprocess.run(
            [
                sys.executable,
                str(handoff),
                str(SCRIPTS.parent / "nixos-rebuild-guard"),
                "boot",
                str(tmp_path / "prepared/request.json"),
            ],
            env=environment,
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert activated.returncode == (99 if contended else 0), activated.stderr
        if contended:
            assert len(read_events(tmp_path)) == command_count
            assert not read_events(tmp_path, "native-events")
        else:
            assert read_events(tmp_path, "native-events")[-1]["action"] == "boot"
    finally:
        if holder is not None:
            stop_holder(holder)
