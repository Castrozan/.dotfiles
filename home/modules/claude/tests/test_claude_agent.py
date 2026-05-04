import importlib.util
import os
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "claude-agent"
loader = importlib.machinery.SourceFileLoader("claude_agent", str(SCRIPT_PATH))
spec = importlib.util.spec_from_loader("claude_agent", loader)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestFindTmuxSocket:
    def test_respects_tmux_tmpdir_env(self, tmp_path):
        socket_dir = tmp_path / "custom-tmux"
        socket_dir.mkdir()
        socket_file = socket_dir / "default"
        socket_file.touch()
        os.mkfifo(str(tmp_path / "decoy"))

        with patch.dict(os.environ, {"TMUX_TMPDIR": str(socket_dir)}):
            with patch.object(Path, "is_socket", return_value=True):
                result = mod.find_tmux_socket()
                assert result == str(socket_file)

    def test_falls_back_to_standard_paths_without_env(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(Path, "exists", return_value=False):
                result = mod.find_tmux_socket()
                assert result is None


class TestValidateProjectDirectory:
    def test_rejects_nonexistent_directory(self, tmp_path):
        with pytest.raises(SystemExit):
            mod.validate_project_directory(tmp_path / "nonexistent")

    def test_rejects_directory_without_claude_md(self, tmp_path):
        with pytest.raises(SystemExit):
            mod.validate_project_directory(tmp_path)

    def test_accepts_directory_with_claude_md(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("test")
        mod.validate_project_directory(tmp_path)


class TestEnsurePmWorkspaceExists:
    def test_creates_pm_directory_and_heartbeat(self, tmp_path):
        result = mod.ensure_pm_workspace_exists(tmp_path)
        assert result == tmp_path / ".pm"
        assert (tmp_path / ".pm").is_dir()
        heartbeat = tmp_path / ".pm" / "HEARTBEAT.md"
        assert heartbeat.exists()
        assert "No active work" in heartbeat.read_text()

    def test_preserves_existing_heartbeat(self, tmp_path):
        pm_dir = tmp_path / ".pm"
        pm_dir.mkdir()
        heartbeat = pm_dir / "HEARTBEAT.md"
        heartbeat.write_text("existing content")
        mod.ensure_pm_workspace_exists(tmp_path)
        assert heartbeat.read_text() == "existing content"


class TestResolvePersistentSessionId:
    def test_generates_deterministic_id(self, tmp_path):
        pm_dir = tmp_path / ".pm"
        pm_dir.mkdir()
        id1 = mod.resolve_persistent_session_id(tmp_path, "myproject")
        stored = (pm_dir / "session-id").read_text().strip()
        assert id1 == stored
        expected = str(
            uuid.uuid5(
                uuid.NAMESPACE_DNS,
                "myproject-project-manager-agent",
            )
        )
        assert id1 == expected

    def test_reuses_existing_session_id(self, tmp_path):
        pm_dir = tmp_path / ".pm"
        pm_dir.mkdir()
        (pm_dir / "session-id").write_text("custom-id\n")
        result = mod.resolve_persistent_session_id(tmp_path, "myproject")
        assert result == "custom-id"


class TestBuildClaudeLaunchCommand:
    def test_uses_session_id_when_not_resuming(self):
        cmd = mod.build_claude_launch_command(
            "opus", "myproject", "abc-123", resume_existing_session=False
        )
        assert "--session-id" in cmd
        assert "--resume" not in cmd

    def test_uses_resume_when_resuming_existing_session(self):
        cmd = mod.build_claude_launch_command(
            "opus", "myproject", "abc-123", resume_existing_session=True
        )
        assert "--resume" in cmd
        assert "--session-id" not in cmd

    def test_appends_single_instructions_file(self):
        cmd = mod.build_claude_launch_command(
            "opus",
            "myproject",
            "abc-123",
            resume_existing_session=False,
            instructions_files=["/nix/store/abc-instructions.md"],
        )
        assert "--append-system-prompt-file" in cmd
        assert "abc-instructions.md" in cmd

    def test_appends_multiple_instructions_files(self):
        cmd = mod.build_claude_launch_command(
            "opus",
            "myproject",
            "abc-123",
            resume_existing_session=False,
            instructions_files=[
                "/nix/store/base-instructions.md",
                "/nix/store/extra-instructions.md",
            ],
        )
        assert cmd.count("--append-system-prompt-file") == 2
        assert "base-instructions.md" in cmd
        assert "extra-instructions.md" in cmd

    def test_quotes_values_with_special_characters(self):
        cmd = mod.build_claude_launch_command(
            "opus 4", "my project", "abc-123", resume_existing_session=False
        )
        assert "'opus 4'" in cmd
        assert "'my project'" in cmd


class TestBuildBootstrapPrompt:
    def test_includes_heartbeat_interval(self):
        prompt = mod.build_bootstrap_prompt("*/15 * * * *")
        assert "*/15 * * * *" in prompt

    def test_includes_onboarding_detection(self):
        prompt = mod.build_bootstrap_prompt("3,33 * * * *")
        assert "No active work" in prompt
        assert "first session" in prompt
        assert "onboarding" in prompt


class TestLoadOrCreateAgentConfig:
    def test_creates_default_config(self, tmp_path):
        config = mod.load_or_create_agent_config(tmp_path, "myproject")
        assert config["name"] == "myproject"
        assert config["model"] == "opus"
        assert (tmp_path / "agent.json").exists()

    def test_loads_existing_config(self, tmp_path):
        import json

        (tmp_path / "agent.json").write_text(
            json.dumps({"name": "custom", "model": "sonnet"})
        )
        config = mod.load_or_create_agent_config(tmp_path, "myproject")
        assert config["name"] == "custom"
        assert config["model"] == "sonnet"


class TestIsChildDirectoryPrunedFromSkillDiscovery:
    def test_prunes_hidden_directories(self):
        assert mod.is_child_directory_pruned_from_skill_discovery(".git") is True
        assert mod.is_child_directory_pruned_from_skill_discovery(".pm") is True
        assert mod.is_child_directory_pruned_from_skill_discovery(".claude") is True

    def test_prunes_known_build_and_cache_directories(self):
        for pruned_directory_name in (
            "node_modules",
            "__pycache__",
            "target",
            "dist",
            "build",
            "venv",
        ):
            assert (
                mod.is_child_directory_pruned_from_skill_discovery(
                    pruned_directory_name
                )
                is True
            )

    def test_keeps_regular_directories(self):
        assert mod.is_child_directory_pruned_from_skill_discovery("packages") is False
        assert mod.is_child_directory_pruned_from_skill_discovery("src") is False
        assert mod.is_child_directory_pruned_from_skill_discovery("skills") is False


class TestDiscoverSkillDirectoriesInProjectTree:
    def test_returns_empty_for_nonexistent_directory(self, tmp_path):
        assert (
            mod.discover_skill_directories_in_project_tree(tmp_path / "missing") == []
        )

    def test_refuses_to_walk_home_directory(self, tmp_path, monkeypatch):
        fake_home_directory = tmp_path / "fake-home"
        fake_home_directory.mkdir()
        nested_skill_directory = fake_home_directory / "project" / "nested-skill"
        nested_skill_directory.mkdir(parents=True)
        (nested_skill_directory / "SKILL.md").write_text("---\nname: nested\n---\n")
        monkeypatch.setenv("HOME", str(fake_home_directory))

        assert mod.discover_skill_directories_in_project_tree(fake_home_directory) == []

    def test_finds_skill_at_project_root(self, tmp_path):
        (tmp_path / "SKILL.md").write_text("---\nname: root\n---\n")
        discovered = mod.discover_skill_directories_in_project_tree(tmp_path)
        assert discovered == [tmp_path.resolve()]

    def test_finds_skills_at_multiple_depths(self, tmp_path):
        first_skill_directory = tmp_path / "packages" / "first-skill"
        first_skill_directory.mkdir(parents=True)
        (first_skill_directory / "SKILL.md").write_text("---\nname: first\n---\n")
        deeper_skill_directory = tmp_path / "cmd" / "agent" / "skills" / "deeper-skill"
        deeper_skill_directory.mkdir(parents=True)
        (deeper_skill_directory / "SKILL.md").write_text("---\nname: deeper\n---\n")

        discovered = mod.discover_skill_directories_in_project_tree(tmp_path)

        assert first_skill_directory.resolve() in discovered
        assert deeper_skill_directory.resolve() in discovered

    def test_skips_hidden_and_pruned_directories(self, tmp_path):
        visible_skill_directory = tmp_path / "visible-skill"
        visible_skill_directory.mkdir()
        (visible_skill_directory / "SKILL.md").write_text("---\nname: visible\n---\n")

        hidden_skill_directory = tmp_path / ".buried" / "hidden-skill"
        hidden_skill_directory.mkdir(parents=True)
        (hidden_skill_directory / "SKILL.md").write_text("---\nname: hidden\n---\n")

        node_modules_skill_directory = (
            tmp_path / "node_modules" / "buried-package-skill"
        )
        node_modules_skill_directory.mkdir(parents=True)
        (node_modules_skill_directory / "SKILL.md").write_text(
            "---\nname: buried\n---\n"
        )

        discovered = mod.discover_skill_directories_in_project_tree(tmp_path)
        assert discovered == [visible_skill_directory.resolve()]

    def test_sorts_by_depth_then_path(self, tmp_path):
        deeper_skill_directory = tmp_path / "a" / "deeper-skill"
        deeper_skill_directory.mkdir(parents=True)
        (deeper_skill_directory / "SKILL.md").write_text("---\nname: deeper\n---\n")
        shallow_skill_directory = tmp_path / "z-shallow-skill"
        shallow_skill_directory.mkdir()
        (shallow_skill_directory / "SKILL.md").write_text("---\nname: shallow\n---\n")

        discovered = mod.discover_skill_directories_in_project_tree(tmp_path)
        assert discovered == [
            shallow_skill_directory.resolve(),
            deeper_skill_directory.resolve(),
        ]


class TestRebuildSkillsShadowDirectoryWithSymlinks:
    def test_returns_none_for_empty_input(self, tmp_path):
        assert mod.rebuild_skills_shadow_directory_with_symlinks(tmp_path, []) is None

    def test_creates_shadow_with_symlinks_named_by_basename(self, tmp_path):
        first_skill_directory = tmp_path / "source" / "first-skill"
        first_skill_directory.mkdir(parents=True)
        (first_skill_directory / "SKILL.md").write_text("---\nname: first\n---\n")
        second_skill_directory = tmp_path / "source" / "second-skill"
        second_skill_directory.mkdir(parents=True)
        (second_skill_directory / "SKILL.md").write_text("---\nname: second\n---\n")

        pm_directory = tmp_path / ".pm"
        pm_directory.mkdir()

        shadow_root = mod.rebuild_skills_shadow_directory_with_symlinks(
            pm_directory, [first_skill_directory, second_skill_directory]
        )

        shadow_skills_directory = shadow_root / ".claude" / "skills"
        assert shadow_root == pm_directory / "skills-shadow"
        first_symlink = shadow_skills_directory / "first-skill"
        second_symlink = shadow_skills_directory / "second-skill"
        assert first_symlink.is_symlink()
        assert second_symlink.is_symlink()
        assert first_symlink.resolve() == first_skill_directory.resolve()
        assert second_symlink.resolve() == second_skill_directory.resolve()

    def test_dedups_by_basename_first_occurrence_wins(self, tmp_path):
        winning_skill_directory = tmp_path / "primary" / "duplicate-name"
        winning_skill_directory.mkdir(parents=True)
        (winning_skill_directory / "SKILL.md").write_text("---\nname: winner\n---\n")
        losing_skill_directory = tmp_path / "secondary" / "duplicate-name"
        losing_skill_directory.mkdir(parents=True)
        (losing_skill_directory / "SKILL.md").write_text("---\nname: loser\n---\n")

        pm_directory = tmp_path / ".pm"
        pm_directory.mkdir()

        shadow_root = mod.rebuild_skills_shadow_directory_with_symlinks(
            pm_directory, [winning_skill_directory, losing_skill_directory]
        )

        deduplicated_symlink = shadow_root / ".claude" / "skills" / "duplicate-name"
        assert deduplicated_symlink.resolve() == winning_skill_directory.resolve()
        assert len(list((shadow_root / ".claude" / "skills").iterdir())) == 1

    def test_removes_existing_shadow_before_rebuild(self, tmp_path):
        pm_directory = tmp_path / ".pm"
        pm_directory.mkdir()
        stale_shadow_directory = pm_directory / "skills-shadow"
        stale_shadow_directory.mkdir()
        stale_marker_file = stale_shadow_directory / "stale-marker.txt"
        stale_marker_file.write_text("from a previous run")

        fresh_skill_directory = tmp_path / "source" / "fresh-skill"
        fresh_skill_directory.mkdir(parents=True)
        (fresh_skill_directory / "SKILL.md").write_text("---\nname: fresh\n---\n")

        mod.rebuild_skills_shadow_directory_with_symlinks(
            pm_directory, [fresh_skill_directory]
        )

        assert not stale_marker_file.exists()
        assert (
            pm_directory / "skills-shadow" / ".claude" / "skills" / "fresh-skill"
        ).is_symlink()


class TestBuildClaudeLaunchCommandAdditionalDirectories:
    def test_appends_add_dir_flag_for_each_additional_directory(self):
        cmd = mod.build_claude_launch_command(
            "opus",
            "myproject",
            "abc-123",
            resume_existing_session=False,
            additional_directories=[
                Path("/tmp/first-shadow"),
                Path("/tmp/second-shadow"),
            ],
        )
        assert cmd.count("--add-dir") == 2
        assert "/tmp/first-shadow" in cmd
        assert "/tmp/second-shadow" in cmd

    def test_omits_add_dir_when_no_additional_directories(self):
        cmd = mod.build_claude_launch_command(
            "opus", "myproject", "abc-123", resume_existing_session=False
        )
        assert "--add-dir" not in cmd
