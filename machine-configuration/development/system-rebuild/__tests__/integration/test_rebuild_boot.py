import subprocess
import time
from pathlib import Path

import pytest


@pytest.fixture
def rebuild_boot_environment(managed_rebuild_environment, tmp_path):
    scripts = Path(__file__).resolve().parents[2] / "scripts"
    backends = tmp_path / "backends"
    backends.mkdir()
    home = tmp_path / "home"
    (home / ".dotfiles").mkdir(parents=True)
    private_entrypoint = home / "zanoni-system"
    private_entrypoint.mkdir()
    (private_entrypoint / "flake.nix").touch()
    entrypoint = tmp_path / "rebuild"
    substitutions = {
        "@machineAlias@": "chise",
        "@backendsDirectory@": str(backends),
        "@exclusiveRunLockHelper@": managed_rebuild_environment[
            "EXCLUSIVE_RUN_LOCK_HELPER"
        ],
        "@exclusiveRunScopePython@": managed_rebuild_environment[
            "EXCLUSIVE_RUN_SCOPE_PYTHON"
        ],
    }
    source = (scripts / "rebuild/rebuild").read_text()
    for placeholder, value in substitutions.items():
        source = source.replace(placeholder, value)
    entrypoint.write_text(source)
    events = tmp_path / "events"
    (backends / "nixos").write_text(
        f'''source "{scripts}/rebuild/backends/nixos"
run_privileged() {{
    printf '%s\\n' "$@" > "{tmp_path}/privileged-arguments"
    while [[ "$1" != nixos-rebuild ]]; do
        if [[ "$1" == DOTFILES_REBUILD_WRAPPER=1 ]]; then export DOTFILES_REBUILD_WRAPPER=1; fi
        shift
    done
    shift
    "{scripts}/nixos-rebuild-guard" "$@"
}}
backend_verify_switch_landed() {{ echo verify >> "{events}"; }}
backend_after_switch() {{ echo desktop >> "{events}"; }}
'''
    )
    native = tmp_path / "native"
    native.write_text(
        f'''#!/usr/bin/env bash
printf '%s\\n' "$@" > "{tmp_path}/native-arguments"
[[ "${{TEST_NATIVE_STATUS:-0}}" == 0 ]] || exit "$TEST_NATIVE_STATUS"
case "$1" in
boot) echo staged > "{tmp_path}/next-generation" ;;
switch) echo active > "{tmp_path}/current-generation"; touch "{tmp_path}/activated" ;;
esac
'''
    )
    native.chmod(0o755)
    (tmp_path / "current-generation").write_text("previous\n")
    return {
        **managed_rebuild_environment,
        "BASH_ENV": "/dev/null",
        "HOME": str(home),
        "MACHINE_LOCAL_ENTRYPOINT_DIRECTORY": str(private_entrypoint),
        "REAL_NIXOS_REBUILD": str(native),
        "TEST_REBUILD_ENTRYPOINT": str(entrypoint),
        "TEST_REBUILD_PLATFORM": "nixos",
        "TEST_EVENTS": str(events),
    }


def run_rebuild(environment, *arguments):
    program = """source "$TEST_REBUILD_ENTRYPOINT"
detect_backend_name() { echo "$TEST_REBUILD_PLATFORM"; }
ensure_nix_is_on_the_path() { echo nix-ready >> "$TEST_EVENTS"; }
initialize_git_submodules() { echo git-ready >> "$TEST_EVENTS"; }
nudge_clawde_agents_to_redeploy_on_continued_sessions() { echo fleet >> "$TEST_EVENTS"; }
main "$@"
"""
    return subprocess.run(
        ["bash", "-c", program, "rebuild-test", *arguments],
        env=environment,
        capture_output=True,
        text=True,
        timeout=5,
    )


def test_boot_stages_native_generation_without_live_or_post_switch_effects(
    rebuild_boot_environment, tmp_path
):
    completed = run_rebuild(rebuild_boot_environment, "boot", "--option", "cores", "2")
    assert completed.returncode == 0, completed.stderr
    arguments = (tmp_path / "native-arguments").read_text().splitlines()
    assert arguments == [
        "boot",
        "--flake",
        f"git+file://{rebuild_boot_environment['HOME']}/zanoni-system#chise",
        "--no-write-lock-file",
        "--option",
        "cores",
        "2",
    ]
    assert (
        "DOTFILES_REBUILD_WRAPPER=1"
        in (tmp_path / "privileged-arguments").read_text().splitlines()
    )
    assert (tmp_path / "next-generation").read_text() == "staged\n"
    assert (tmp_path / "current-generation").read_text() == "previous\n"
    assert not (tmp_path / "activated").exists()
    assert (tmp_path / "events").read_text().splitlines() == ["nix-ready", "git-ready"]
    assert "reboot to activate" in completed.stdout


def test_default_switch_preserves_live_activation_and_post_switch_effects(
    rebuild_boot_environment, tmp_path
):
    completed = run_rebuild(rebuild_boot_environment, "--option", "cores", "2")
    assert completed.returncode == 0, completed.stderr
    assert (tmp_path / "native-arguments").read_text().splitlines()[0] == "switch"
    assert (tmp_path / "current-generation").read_text() == "active\n"
    assert (tmp_path / "activated").exists()
    assert (tmp_path / "events").read_text().splitlines() == [
        "nix-ready",
        "git-ready",
        "verify",
        "desktop",
        "fleet",
    ]


@pytest.mark.parametrize("platform", ["darwin", "home-manager"])
def test_unsupported_boot_fails_before_environment_or_expensive_preparation(
    rebuild_boot_environment, tmp_path, platform
):
    completed = run_rebuild(
        {**rebuild_boot_environment, "TEST_REBUILD_PLATFORM": platform}, "boot"
    )
    assert completed.returncode == 1
    assert "supported only on NixOS" in completed.stderr
    for name in ("events", "native-arguments", "privileged-arguments"):
        assert not (tmp_path / name).exists()


def test_boot_preserves_private_entrypoint_refusal(rebuild_boot_environment, tmp_path):
    (Path(rebuild_boot_environment["HOME"]) / "zanoni-system/flake.nix").unlink()
    completed = run_rebuild(rebuild_boot_environment, "boot")
    assert completed.returncode == 1
    assert "refusing to deploy chise from bare" in completed.stderr
    assert not (tmp_path / "native-arguments").exists()


def test_failed_boot_preserves_native_status_and_skips_post_switch_effects(
    rebuild_boot_environment, tmp_path
):
    completed = run_rebuild(
        {**rebuild_boot_environment, "TEST_NATIVE_STATUS": "42"}, "boot"
    )
    assert completed.returncode == 42
    assert (tmp_path / "current-generation").read_text() == "previous\n"
    assert not (tmp_path / "next-generation").exists()
    assert (tmp_path / "events").read_text().splitlines() == ["nix-ready", "git-ready"]


def test_boot_contends_with_an_existing_managed_rebuild(
    rebuild_boot_environment, tmp_path
):
    acquired = tmp_path / "acquired"
    holder = subprocess.Popen(
        [
            rebuild_boot_environment["SYSTEM_REBUILD_LOCK_GUARD"],
            "bash",
            "-c",
            f'touch "{acquired}"; sleep 30',
        ],
        env=rebuild_boot_environment,
        start_new_session=True,
    )
    try:
        deadline = time.monotonic() + 5
        while not acquired.exists():
            assert time.monotonic() < deadline
            time.sleep(0.01)
        completed = run_rebuild(rebuild_boot_environment, "boot")
        assert completed.returncode == 99, completed.stderr
        assert "LOCKED_BY_CONCURRENT_RUN" in completed.stderr
        assert not (tmp_path / "native-arguments").exists()
    finally:
        holder.terminate()
        holder.wait(timeout=5)
