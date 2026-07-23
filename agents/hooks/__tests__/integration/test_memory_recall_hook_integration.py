import json


class TestHookSilentPaths:
    def test_exits_silently_when_memory_directory_does_not_exist(
        self,
        tmp_path,
        isolated_memory_recall_environment,
        invoke_memory_recall_hook,
    ):
        workspace = tmp_path / "no-memory"
        workspace.mkdir()
        result = invoke_memory_recall_hook(
            {
                "cwd": str(workspace),
                "tool_input": {"command": "ls -la"},
                "session_id": "test-no-memory",
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_exits_silently_when_no_keywords(
        self,
        tmp_path,
        isolated_memory_recall_environment,
        invoke_memory_recall_hook,
        make_memory_recall_directory,
    ):
        fake_home, _ = isolated_memory_recall_environment
        workspace = tmp_path / "ws-empty-input"
        workspace.mkdir()
        memory_dir = make_memory_recall_directory(fake_home, workspace)
        (memory_dir / "user-x.md").write_text("# user-x\n\n- fact\n")
        result = invoke_memory_recall_hook(
            {
                "cwd": str(workspace),
                "tool_input": {"command": "is the a of"},
                "session_id": "test-no-keywords",
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_exits_silently_when_memory_has_no_matches(
        self,
        tmp_path,
        isolated_memory_recall_environment,
        invoke_memory_recall_hook,
        make_memory_recall_directory,
    ):
        fake_home, _ = isolated_memory_recall_environment
        workspace = tmp_path / "ws-no-match"
        workspace.mkdir()
        memory_dir = make_memory_recall_directory(fake_home, workspace)
        (memory_dir / "user-x.md").write_text(
            "# user-x\n\n- lucas prefers vim over emacs\n"
        )
        result = invoke_memory_recall_hook(
            {
                "cwd": str(workspace),
                "tool_input": {"command": "deploy kubernetes cluster"},
                "session_id": "test-no-match",
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""


class TestHookRecallEmission:
    def test_emits_recall_when_keywords_match_topic_file(
        self,
        tmp_path,
        isolated_memory_recall_environment,
        invoke_memory_recall_hook,
        make_memory_recall_directory,
    ):
        fake_home, _ = isolated_memory_recall_environment
        workspace = tmp_path / "ws-match"
        workspace.mkdir()
        memory_dir = make_memory_recall_directory(fake_home, workspace)
        (memory_dir / "user-lucas.md").write_text(
            "# user-lucas\n\n- 2026-05-17: lucas prefers pnpm over npm for js projects\n"
        )
        result = invoke_memory_recall_hook(
            {
                "cwd": str(workspace),
                "tool_input": {"command": "pnpm install discord-bot"},
                "session_id": "test-match",
            }
        )
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        additional_context = parsed["hookSpecificOutput"]["additionalContext"]
        assert "Recall:" in additional_context
        assert "user-lucas.md" in additional_context

    def test_ignores_memory_index_file_in_recall(
        self,
        tmp_path,
        isolated_memory_recall_environment,
        invoke_memory_recall_hook,
        make_memory_recall_directory,
    ):
        fake_home, _ = isolated_memory_recall_environment
        workspace = tmp_path / "ws-ignore-index"
        workspace.mkdir()
        memory_dir = make_memory_recall_directory(fake_home, workspace)
        (memory_dir / "MEMORY.md").write_text(
            "# Memory index\n\n- [user/x](user-x.md): pnpm preference\n"
        )
        (memory_dir / "user-x.md").write_text(
            "# user-x\n\n- 2026-05-17: pnpm is preferred\n"
        )
        result = invoke_memory_recall_hook(
            {
                "cwd": str(workspace),
                "tool_input": {"command": "pnpm test"},
                "session_id": "test-ignore-index",
            }
        )
        parsed = json.loads(result.stdout)
        additional_context = parsed["hookSpecificOutput"]["additionalContext"]
        assert "MEMORY.md" not in additional_context
        assert "user-x.md" in additional_context


class TestArchiveExclusion:
    def test_does_not_emit_recall_from_archive_subdirectory(
        self,
        tmp_path,
        isolated_memory_recall_environment,
        invoke_memory_recall_hook,
        make_memory_recall_directory,
    ):
        fake_home, _ = isolated_memory_recall_environment
        workspace = tmp_path / "ws-archive"
        workspace.mkdir()
        memory_dir = make_memory_recall_directory(fake_home, workspace)
        (memory_dir / "archive").mkdir()
        (memory_dir / "archive" / "user-old.md").write_text(
            "# user-old\n\n- 2025-01-01: lucas used to prefer pnpm\n"
        )
        result = invoke_memory_recall_hook(
            {
                "cwd": str(workspace),
                "tool_input": {"command": "pnpm install"},
                "session_id": "test-archive-exclusion",
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""
