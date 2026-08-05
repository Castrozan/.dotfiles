import os
import subprocess
import sys
from pathlib import Path


def test_shared_entries_become_symlinks_back_into_the_shared_config(run_seed):
    invoke, isolated = run_seed
    assert invoke().returncode == 0
    for shared_name in ("skills", "CLAUDE.md"):
        linked = isolated / shared_name
        assert linked.is_symlink(), f"{shared_name} must be shared through a symlink"
        assert Path(os.readlink(linked)).name == shared_name


def test_plugins_stay_isolated_instead_of_pointing_at_the_shared_plugins(run_seed):
    invoke, isolated = run_seed
    assert invoke().returncode == 0
    isolated_plugins = isolated / "plugins"
    assert isolated_plugins.is_dir()
    assert not isolated_plugins.is_symlink(), (
        "plugins must stay isolated, otherwise a work-only plugin leaks into every session"
    )
    assert not (isolated_plugins / "shared-plugin.json").exists()


def test_a_symlink_pointing_at_the_wrong_target_is_repointed(run_seed, tmp_path):
    invoke, isolated = run_seed
    isolated.mkdir(parents=True)
    stale_target = tmp_path / "stale-skills"
    stale_target.mkdir()
    (isolated / "skills").symlink_to(stale_target)

    assert invoke().returncode == 0
    assert Path(os.readlink(isolated / "skills")).name == "skills"


def test_a_missing_shared_config_directory_fails_loudly(
    tmp_path, settings_overlay_file, seed_config_dir_overlay_script_path
):
    completed = subprocess.run(
        [
            sys.executable,
            str(seed_config_dir_overlay_script_path),
            "--source-config-directory",
            str(tmp_path / "absent"),
            "--target-config-directory",
            str(tmp_path / "isolated"),
            "--settings-overlay-file",
            str(settings_overlay_file),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode != 0
    assert "does not exist" in completed.stderr
