class TestHookDebounceIntegration:
    def test_second_fire_with_same_keywords_is_silent(
        self,
        tmp_path,
        isolated_memory_recall_environment,
        invoke_memory_recall_hook,
        make_memory_recall_directory,
    ):
        fake_home, _ = isolated_memory_recall_environment
        workspace = tmp_path / "ws-debounce"
        workspace.mkdir()
        memory_dir = make_memory_recall_directory(fake_home, workspace)
        (memory_dir / "user-x.md").write_text(
            "# user-x\n\n- 2026-05-17: pnpm is preferred\n"
        )
        payload = {
            "cwd": str(workspace),
            "tool_input": {"command": "pnpm install"},
            "session_id": "test-debounce-same",
        }
        first = invoke_memory_recall_hook(payload)
        second = invoke_memory_recall_hook(payload)
        assert first.returncode == 0
        assert second.returncode == 0
        assert first.stdout != ""
        assert second.stdout == ""

    def test_different_session_does_not_debounce(
        self,
        tmp_path,
        isolated_memory_recall_environment,
        invoke_memory_recall_hook,
        make_memory_recall_directory,
    ):
        fake_home, _ = isolated_memory_recall_environment
        workspace = tmp_path / "ws-debounce-session"
        workspace.mkdir()
        memory_dir = make_memory_recall_directory(fake_home, workspace)
        (memory_dir / "user-x.md").write_text(
            "# user-x\n\n- 2026-05-17: pnpm is preferred\n"
        )
        first = invoke_memory_recall_hook(
            {
                "cwd": str(workspace),
                "tool_input": {"command": "pnpm install"},
                "session_id": "session-one",
            }
        )
        second = invoke_memory_recall_hook(
            {
                "cwd": str(workspace),
                "tool_input": {"command": "pnpm install"},
                "session_id": "session-two",
            }
        )
        assert first.stdout != ""
        assert second.stdout != ""
