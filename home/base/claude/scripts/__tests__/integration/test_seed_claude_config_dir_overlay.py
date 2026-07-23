import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SEED_SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent.parent / "seed-claude-config-dir-overlay"
)


@pytest.fixture
def shared_config_directory(tmp_path):
    home = tmp_path / "home"
    shared = home / ".claude"
    (shared / "skills" / "git").mkdir(parents=True)
    (shared / "skills" / "git" / "SKILL.md").write_text("shared skill body")
    (shared / "plugins").mkdir()
    (shared / "plugins" / "shared-plugin.json").write_text("{}")
    (shared / "CLAUDE.md").write_text("shared core rules")
    (shared / "settings.json").write_text(
        json.dumps({"model": "opus", "theme": "dark", "voice": "off"})
    )
    (home / ".claude.json").write_text(json.dumps({"installMethod": "shared"}))
    return shared


@pytest.fixture
def settings_overlay_file(tmp_path):
    overlay_path = tmp_path / "overlay.json"
    overlay_path.write_text(
        json.dumps({"model": "sonnet", "enabledPlugins": {"work": True}})
    )
    return overlay_path


@pytest.fixture
def run_seed(tmp_path, shared_config_directory, settings_overlay_file):
    isolated = tmp_path / "isolated-config"

    def invoke() -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                str(SEED_SCRIPT_PATH),
                "--source-config-directory",
                str(shared_config_directory),
                "--target-config-directory",
                str(isolated),
                "--settings-overlay-file",
                str(settings_overlay_file),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

    return invoke, isolated


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


def test_settings_are_a_real_file_merging_the_overlay_onto_the_shared_settings(
    run_seed,
):
    invoke, isolated = run_seed
    assert invoke().returncode == 0
    isolated_settings = isolated / "settings.json"
    assert not isolated_settings.is_symlink()
    settings = json.loads(isolated_settings.read_text())
    assert settings["model"] == "sonnet", "the overlay must win on a key collision"
    assert settings["theme"] == "dark", "shared keys the overlay omits must survive"
    assert settings["enabledPlugins"] == {"work": True}


def test_settings_are_owner_readable_only(run_seed):
    invoke, isolated = run_seed
    assert invoke().returncode == 0
    assert (isolated / "settings.json").stat().st_mode & 0o777 == 0o600


def test_a_second_run_keeps_runtime_keys_written_into_the_isolated_settings(run_seed):
    invoke, isolated = run_seed
    assert invoke().returncode == 0
    isolated_settings = isolated / "settings.json"
    settings = json.loads(isolated_settings.read_text())
    settings["voiceEnabled"] = True
    isolated_settings.write_text(json.dumps(settings))

    assert invoke().returncode == 0
    reseeded = json.loads(isolated_settings.read_text())
    assert reseeded["voiceEnabled"] is True, "reseeding must not clobber runtime keys"
    assert reseeded["model"] == "sonnet", "reseeding must reapply the declared overlay"


def test_the_isolated_claude_json_is_seeded_once_and_then_left_alone(run_seed):
    invoke, isolated = run_seed
    assert invoke().returncode == 0
    isolated_claude_json = isolated / ".claude.json"
    assert json.loads(isolated_claude_json.read_text())["installMethod"] == "shared"
    isolated_claude_json.write_text(json.dumps({"installMethod": "edited-at-runtime"}))

    assert invoke().returncode == 0
    assert (
        json.loads(isolated_claude_json.read_text())["installMethod"]
        == "edited-at-runtime"
    ), "the isolated .claude.json holds live session state and must not be reseeded"


def test_a_symlink_pointing_at_the_wrong_target_is_repointed(run_seed, tmp_path):
    invoke, isolated = run_seed
    isolated.mkdir(parents=True)
    stale_target = tmp_path / "stale-skills"
    stale_target.mkdir()
    (isolated / "skills").symlink_to(stale_target)

    assert invoke().returncode == 0
    assert Path(os.readlink(isolated / "skills")).name == "skills"


def test_a_missing_shared_config_directory_fails_loudly(
    tmp_path, settings_overlay_file
):
    completed = subprocess.run(
        [
            sys.executable,
            str(SEED_SCRIPT_PATH),
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
