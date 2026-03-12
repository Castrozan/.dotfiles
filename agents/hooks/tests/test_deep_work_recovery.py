import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

import deep_work_recovery as dwr


class TestFindActiveDeepWorkWorkspaces:
    def test_returns_empty_when_no_deep_work_directory(self, tmp_path):
        assert dwr.find_active_deep_work_workspaces(str(tmp_path)) == []

    def test_returns_empty_when_deep_work_directory_is_empty(self, tmp_path):
        (tmp_path / ".deep-work").mkdir()
        assert dwr.find_active_deep_work_workspaces(str(tmp_path)) == []

    def test_returns_workspace_with_plan_file(self, tmp_path):
        workspace = tmp_path / ".deep-work" / "my-task"
        workspace.mkdir(parents=True)
        (workspace / "plan.md").write_text("# Plan")

        result = dwr.find_active_deep_work_workspaces(str(tmp_path))
        assert len(result) == 1
        assert result[0].name == "my-task"

    def test_skips_workspace_without_plan_file(self, tmp_path):
        workspace = tmp_path / ".deep-work" / "incomplete"
        workspace.mkdir(parents=True)
        (workspace / "prompts.md").write_text("some prompt")

        assert dwr.find_active_deep_work_workspaces(str(tmp_path)) == []

    def test_returns_multiple_workspaces_sorted(self, tmp_path):
        for name in ["beta-task", "alpha-task"]:
            workspace = tmp_path / ".deep-work" / name
            workspace.mkdir(parents=True)
            (workspace / "plan.md").write_text(f"# {name}")

        result = dwr.find_active_deep_work_workspaces(str(tmp_path))
        assert [workspace.name for workspace in result] == ["alpha-task", "beta-task"]

    def test_ignores_files_in_deep_work_directory(self, tmp_path):
        deep_work = tmp_path / ".deep-work"
        deep_work.mkdir()
        (deep_work / "README.md").write_text("ignore me")

        assert dwr.find_active_deep_work_workspaces(str(tmp_path)) == []


class TestReadFileHead:
    def test_reads_short_file_completely(self, tmp_path):
        file = tmp_path / "short.md"
        file.write_text("line1\nline2\nline3")

        result = dwr.read_file_head(file)
        assert result == "line1\nline2\nline3"

    def test_truncates_long_file(self, tmp_path):
        file = tmp_path / "long.md"
        file.write_text("\n".join(f"line{i}" for i in range(50)))

        result = dwr.read_file_head(file, max_lines=3)
        assert "line0" in result
        assert "line2" in result
        assert "line3" not in result
        assert "more lines" in result

    def test_returns_empty_for_missing_file(self):
        assert dwr.read_file_head(Path("/nonexistent/file.md")) == ""


class TestReadFileTail:
    def test_reads_last_lines(self, tmp_path):
        file = tmp_path / "log.md"
        file.write_text("\n".join(f"entry{i}" for i in range(20)))

        result = dwr.read_file_tail(file, max_lines=3)
        assert "entry17" in result
        assert "entry18" in result
        assert "entry19" in result
        assert "earlier entries" in result

    def test_reads_full_file_when_shorter_than_limit(self, tmp_path):
        file = tmp_path / "short.md"
        file.write_text("only\ntwo\nlines")

        result = dwr.read_file_tail(file, max_lines=10)
        assert "only" in result
        assert "earlier entries" not in result

    def test_returns_empty_for_missing_file(self):
        assert dwr.read_file_tail(Path("/nonexistent/file.md")) == ""


class TestBuildWorkspaceRecoverySummary:
    def test_includes_plan_and_progress(self, tmp_path):
        workspace = tmp_path / "my-task"
        workspace.mkdir()
        (workspace / "plan.md").write_text(
            "## Phase 1\n- [x] Done\n## Phase 2\n- [ ] Pending"
        )
        (workspace / "progress.md").write_text("2026-03-12: Completed phase 1")

        result = dwr.build_workspace_recovery_summary(workspace)
        assert "my-task" in result
        assert "Phase 1" in result
        assert "Completed phase 1" in result

    def test_includes_context_file(self, tmp_path):
        workspace = tmp_path / "my-task"
        workspace.mkdir()
        (workspace / "plan.md").write_text("# Plan")
        (workspace / "context.md").write_text("Key constraint: must use Python 3.12")

        result = dwr.build_workspace_recovery_summary(workspace)
        assert "must use Python 3.12" in result

    def test_includes_prompts_file_pointer(self, tmp_path):
        workspace = tmp_path / "my-task"
        workspace.mkdir()
        (workspace / "plan.md").write_text("# Plan")
        (workspace / "prompts.md").write_text("User said: build everything")

        result = dwr.build_workspace_recovery_summary(workspace)
        assert "prompts" in result
        assert "read full file" in result

    def test_handles_workspace_with_only_plan(self, tmp_path):
        workspace = tmp_path / "minimal"
        workspace.mkdir()
        (workspace / "plan.md").write_text("# Plan\nJust started")

        result = dwr.build_workspace_recovery_summary(workspace)
        assert "minimal" in result
        assert "Just started" in result


class TestCheckHeartbeatFile:
    def test_returns_empty_when_no_heartbeat(self, tmp_path):
        assert dwr.check_heartbeat_file(str(tmp_path)) == ""

    def test_returns_empty_for_empty_heartbeat(self, tmp_path):
        (tmp_path / "HEARTBEAT.md").write_text("")
        assert dwr.check_heartbeat_file(str(tmp_path)) == ""

    def test_returns_content_for_active_heartbeat(self, tmp_path):
        (tmp_path / "HEARTBEAT.md").write_text(
            "# Active: Big refactor\nNext: finish module B"
        )

        result = dwr.check_heartbeat_file(str(tmp_path))
        assert "Big refactor" in result
        assert "HEARTBEAT" in result


class TestMain:
    def test_exits_silently_on_non_session_start_event(self):
        input_data = json.dumps({"hook_event_name": "PreToolUse"})
        with patch("sys.stdin", StringIO(input_data)):
            with pytest.raises(SystemExit) as exc_info:
                dwr.main()
            assert exc_info.value.code == 0

    def test_exits_silently_when_no_active_work(self, tmp_path):
        input_data = json.dumps({"hook_event_name": "SessionStart"})
        with patch("sys.stdin", StringIO(input_data)):
            with patch("os.getcwd", return_value=str(tmp_path)):
                with pytest.raises(SystemExit) as exc_info:
                    dwr.main()
                assert exc_info.value.code == 0

    def test_outputs_recovery_context_when_workspace_exists(self, tmp_path, capsys):
        workspace = tmp_path / ".deep-work" / "active-task"
        workspace.mkdir(parents=True)
        (workspace / "plan.md").write_text("# Plan\n- [ ] Step 1")
        (workspace / "progress.md").write_text("Did step 0")

        input_data = json.dumps({"hook_event_name": "SessionStart"})
        with patch("sys.stdin", StringIO(input_data)):
            with patch("os.getcwd", return_value=str(tmp_path)):
                with pytest.raises(SystemExit) as exc_info:
                    dwr.main()
                assert exc_info.value.code == 0

        output = capsys.readouterr().out
        parsed = json.loads(output)
        assert parsed["continue"] is True
        assert "DEEP-WORK RECOVERY" in parsed["hookSpecificOutput"]["additionalContext"]
        assert "active-task" in parsed["hookSpecificOutput"]["additionalContext"]
        assert "Resume from disk" in parsed["hookSpecificOutput"]["additionalContext"]

    def test_outputs_heartbeat_when_present(self, tmp_path, capsys):
        (tmp_path / "HEARTBEAT.md").write_text("# Active: quick fix\nDoing something")

        input_data = json.dumps({"hook_event_name": "SessionStart"})
        with patch("sys.stdin", StringIO(input_data)):
            with patch("os.getcwd", return_value=str(tmp_path)):
                with pytest.raises(SystemExit) as exc_info:
                    dwr.main()
                assert exc_info.value.code == 0

        output = capsys.readouterr().out
        parsed = json.loads(output)
        assert "HEARTBEAT" in parsed["hookSpecificOutput"]["additionalContext"]

    def test_exits_on_invalid_json(self):
        with patch("sys.stdin", StringIO("not json")):
            with pytest.raises(SystemExit) as exc_info:
                dwr.main()
            assert exc_info.value.code == 1
