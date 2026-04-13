import importlib.util
import os
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "launch-project-agent"
loader = importlib.machinery.SourceFileLoader("launch_project_agent", str(SCRIPT_PATH))
spec = importlib.util.spec_from_loader("launch_project_agent", loader)
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
    def test_always_uses_session_id(self):
        cmd = mod.build_claude_launch_command("opus", "myproject", "abc-123")
        assert "--session-id" in cmd
        assert "--resume" not in cmd

    def test_appends_instructions_file(self):
        cmd = mod.build_claude_launch_command(
            "opus",
            "myproject",
            "abc-123",
            instructions_file="/nix/store/abc-instructions.md",
        )
        assert "--append-system-prompt-file" in cmd
        assert "abc-instructions.md" in cmd

    def test_quotes_values_with_special_characters(self):
        cmd = mod.build_claude_launch_command("opus 4", "my project", "abc-123")
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
