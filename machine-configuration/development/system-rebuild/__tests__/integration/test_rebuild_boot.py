import subprocess
import re
import time
from pathlib import Path

import pytest


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
    assert (tmp_path / "events").read_text().splitlines() == [
        "nix-ready",
        "git-ready",
        "prefetch",
        "privileged",
    ]
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
        "prefetch",
        "privileged",
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
    assert (tmp_path / "events").read_text().splitlines() == [
        "nix-ready",
        "git-ready",
        "prefetch",
        "privileged",
    ]


def test_prefetch_failure_prevents_privilege_handoff(
    rebuild_boot_environment, tmp_path
):
    completed = run_rebuild(
        {**rebuild_boot_environment, "TEST_PREFETCH_STATUS": "42"}, "boot"
    )
    assert completed.returncode == 42
    assert not (tmp_path / "privileged-arguments").exists()
    assert (tmp_path / "events").read_text().splitlines() == [
        "nix-ready",
        "git-ready",
        "prefetch",
    ]


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


@pytest.mark.parametrize(
    "capability", ["NIXOS_REBUILD_PREFETCH", "NIXOS_STAGED_REBUILD"]
)
def test_missing_staged_infrastructure_fails_before_prefetch_or_sudo(
    rebuild_boot_environment, tmp_path, capability
):
    entrypoint = Path(rebuild_boot_environment["TEST_REBUILD_ENTRYPOINT"])
    entrypoint.write_text(
        re.sub(
            rf"readonly {capability}=.*",
            f'readonly {capability}="{tmp_path}/absent"',
            entrypoint.read_text(),
        )
    )
    completed = run_rebuild(rebuild_boot_environment, "boot")
    assert completed.returncode == 1
    assert "infrastructure is missing" in completed.stderr
    assert not (tmp_path / "prefetch-arguments").exists()
    assert not (tmp_path / "privileged-arguments").exists()
