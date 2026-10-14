import subprocess

import pytest

from e2e.sessions.e2e_workspace import setup_e2e_scenario_workspace


def test_scenario_workspace_ignores_global_git_hooks(tmp_path, monkeypatch):
    hooks_directory = tmp_path / "hooks"
    hooks_directory.mkdir()
    rejecting_hook = hooks_directory / "commit-msg"
    rejecting_hook.write_text("#!/bin/sh\nexit 1\n")
    rejecting_hook.chmod(0o755)

    global_git_config = tmp_path / "gitconfig"
    subprocess.run(
        [
            "git",
            "config",
            "--file",
            str(global_git_config),
            "core.hooksPath",
            str(hooks_directory),
        ],
        check=True,
    )
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(global_git_config))

    workspace_directory = tmp_path / "workspace"
    workspace_directory.mkdir()
    setup_e2e_scenario_workspace({"setup": {"git_init": True}}, workspace_directory)

    result = subprocess.run(
        ["git", "log", "-1", "--format=%s"],
        cwd=workspace_directory,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "initial"


def test_scenario_workspace_installs_declared_project_skill(tmp_path):
    workspace_directory = tmp_path / "workspace"
    workspace_directory.mkdir()

    setup_e2e_scenario_workspace(
        {"setup": {"project_skills": ["nix"]}}, workspace_directory
    )

    skill_directory = workspace_directory / ".claude" / "skills" / "nix"
    assert skill_directory.is_symlink()
    assert (skill_directory / "SKILL.md").is_file()


def test_scenario_workspace_rejects_unknown_project_skill(tmp_path):
    workspace_directory = tmp_path / "workspace"
    workspace_directory.mkdir()

    with pytest.raises(ValueError, match="unknown project skill: unknown"):
        setup_e2e_scenario_workspace(
            {"setup": {"project_skills": ["unknown"]}}, workspace_directory
        )
