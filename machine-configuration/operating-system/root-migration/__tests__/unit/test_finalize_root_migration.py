import os
from pathlib import Path
import subprocess

import pytest


SCRIPT_DIRECTORY = Path(__file__).resolve().parents[2] / "scripts"
SOURCE_UUID = "11111111-1111-1111-1111-111111111111"
DESTINATION_UUID = "22222222-2222-2222-2222-222222222222"
MIGRATION_IDENTITY = f"{SOURCE_UUID}:{DESTINATION_UUID}"


@pytest.fixture
def migration_environment(tmp_path):
    destination = tmp_path / "destination"
    state = destination / ".root-migration"
    state.mkdir(parents=True)
    (state / "prepared").write_text(MIGRATION_IDENTITY + "\n")
    commands = tmp_path / "commands"
    commands.mkdir()
    command_script = """#!/bin/sh
set -eu
command_name=${0##*/}
printf '%s %s\\n' "$command_name" "$*" >> "$COMMAND_LOG"
case "$command_name" in
findmnt)
  case "$*" in
    *--source*) exit "${SOURCE_MOUNTED_STATUS:-1}" ;;
    *UUID*) printf '%s\\n' "${MOUNTED_UUID:-$DESTINATION_UUID}" ;;
    *OPTIONS*) printf '%s\\n' "${SOURCE_OPTIONS:-ro,relatime}" ;;
  esac
  ;;
blkid) printf '%s\\n' "$SOURCE_UUID" ;;
mount)
  for argument do mount_directory=$argument; done
  mkdir -p "$mount_directory/etc"
  if [ "${MISSING_NIXOS:-0}" = 0 ]; then touch "$mount_directory/etc/NIXOS"; fi
  ;;
umount)
  rm -f "$1/etc/NIXOS"
  rmdir "$1/etc"
  ;;
rsync) exit "${RSYNC_STATUS:-0}" ;;
sync) ;;
esac
"""
    for name in ("findmnt", "blkid", "mount", "umount", "rsync", "sync"):
        command = commands / name
        command.write_text(command_script)
        command.chmod(0o755)
    environment = os.environ | {
        "PATH": f"{commands}:{os.environ['PATH']}",
        "TMPDIR": str(tmp_path),
        "SOURCE_UUID": SOURCE_UUID,
        "DESTINATION_UUID": DESTINATION_UUID,
        "COMMAND_LOG": str(tmp_path / "commands.log"),
    }
    return destination, state, environment


def run_migration(migration_environment, **overrides):
    destination, _, environment = migration_environment
    return subprocess.run(
        [
            "sh",
            str(SCRIPT_DIRECTORY / "finalize-root-migration.sh"),
            SOURCE_UUID,
            DESTINATION_UUID,
            str(destination),
            str(SCRIPT_DIRECTORY / "root-copy-excludes"),
        ],
        env=environment | overrides,
        text=True,
        capture_output=True,
        check=False,
    )


def read_commands(migration_environment):
    command_log = Path(migration_environment[2]["COMMAND_LOG"])
    return command_log.read_text() if command_log.exists() else ""


def test_refuses_an_unprepared_copy(migration_environment):
    _, state, _ = migration_environment
    (state / "prepared").unlink()
    result = run_migration(migration_environment)
    assert result.returncode != 0
    assert "not been prepared" in result.stderr
    assert "rsync " not in read_commands(migration_environment)


def test_refuses_the_wrong_destination(migration_environment):
    result = run_migration(migration_environment, MOUNTED_UUID=SOURCE_UUID)
    assert result.returncode != 0
    assert "wrong filesystem UUID" in result.stderr
    assert "mount -t" not in read_commands(migration_environment)


def test_refuses_an_already_mounted_source(migration_environment):
    result = run_migration(migration_environment, SOURCE_MOUNTED_STATUS="0")
    assert result.returncode != 0
    assert "already mounted" in result.stderr
    assert "mount -t" not in read_commands(migration_environment)


def test_refuses_a_writable_source_and_unmounts_it(migration_environment):
    result = run_migration(migration_environment, SOURCE_OPTIONS="rw,relatime")
    assert result.returncode != 0
    assert "not read-only" in result.stderr
    commands = read_commands(migration_environment)
    assert "rsync " not in commands
    assert "umount " in commands


def test_refuses_a_non_nixos_source(migration_environment):
    result = run_migration(migration_environment, MISSING_NIXOS="1")
    assert result.returncode != 0
    assert "not a NixOS root" in result.stderr
    assert "rsync " not in read_commands(migration_environment)


@pytest.mark.parametrize("status", ["11", "23", "24"])
def test_failed_copy_never_marks_completion(migration_environment, status):
    _, state, _ = migration_environment
    result = run_migration(migration_environment, RSYNC_STATUS=status)
    assert result.returncode != 0
    assert not (state / "completed").exists()
    assert "umount " in read_commands(migration_environment)


def test_commits_completion_after_copy_unmount_and_sync(migration_environment):
    _, state, _ = migration_environment
    result = run_migration(migration_environment)
    assert result.returncode == 0, result.stderr
    assert (state / "completed").read_text().strip() == MIGRATION_IDENTITY
    commands = [
        line.split()[0] for line in read_commands(migration_environment).splitlines()
    ]
    assert commands.index("rsync") < commands.index("umount") < commands.index("sync")


def test_completed_migration_never_reads_the_old_root_again(migration_environment):
    _, state, _ = migration_environment
    (state / "completed").write_text(MIGRATION_IDENTITY + "\n")
    (state / "prepared").unlink()
    result = run_migration(migration_environment)
    assert result.returncode == 0
    commands = read_commands(migration_environment)
    assert "blkid " not in commands
    assert "rsync " not in commands


@pytest.mark.parametrize("marker", ["prepared", "completed"])
def test_refuses_a_marker_from_another_migration(migration_environment, marker):
    _, state, _ = migration_environment
    (state / marker).write_text("another-migration\n")
    result = run_migration(migration_environment)
    assert result.returncode != 0
    assert "another migration" in result.stderr
    assert "rsync " not in read_commands(migration_environment)
