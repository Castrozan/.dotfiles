import json
import time

import memory_recall


class TestHookSessionBudgetHardStop:
    def test_exhausted_event_budget_suppresses_emit(
        self,
        tmp_path,
        isolated_memory_recall_environment,
        invoke_memory_recall_hook,
        make_memory_recall_directory,
    ):
        fake_home, _ = isolated_memory_recall_environment
        workspace = tmp_path / "ws-budget"
        workspace.mkdir()
        memory_dir = make_memory_recall_directory(fake_home, workspace)
        (memory_dir / "user-x.md").write_text(
            "# user-x\n\n- 2026-05-17: pnpm is preferred\n"
        )
        session_id = "session-budget-exhausted"
        state_path = memory_recall.debounce_state_path_for_session(session_id)
        state_path.write_text(
            json.dumps(
                {"recall_event_count": memory_recall.SESSION_RECALL_EVENT_BUDGET}
            )
        )
        result = invoke_memory_recall_hook(
            {
                "cwd": str(workspace),
                "tool_input": {"command": "pnpm install"},
                "session_id": session_id,
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_fresh_session_below_budget_still_emits(
        self,
        tmp_path,
        isolated_memory_recall_environment,
        invoke_memory_recall_hook,
        make_memory_recall_directory,
    ):
        fake_home, _ = isolated_memory_recall_environment
        workspace = tmp_path / "ws-budget-control"
        workspace.mkdir()
        memory_dir = make_memory_recall_directory(fake_home, workspace)
        (memory_dir / "user-x.md").write_text(
            "# user-x\n\n- 2026-05-17: pnpm is preferred\n"
        )
        result = invoke_memory_recall_hook(
            {
                "cwd": str(workspace),
                "tool_input": {"command": "pnpm install"},
                "session_id": "session-budget-fresh",
            }
        )
        assert result.returncode == 0
        assert result.stdout != ""


class TestHookPathSetDedup:
    def _seed_recent_state(self, session_id, injected_hashes):
        state_path = memory_recall.debounce_state_path_for_session(session_id)
        state_path.write_text(
            json.dumps(
                {
                    "last_fire_timestamp": time.time() - 100,
                    "last_keywords": ["unrelated-keyword"],
                    "injected_recall_path_set_hashes": injected_hashes,
                }
            )
        )

    def test_already_injected_path_set_is_suppressed_outside_debounce_window(
        self,
        tmp_path,
        isolated_memory_recall_environment,
        invoke_memory_recall_hook,
        make_memory_recall_directory,
    ):
        fake_home, _ = isolated_memory_recall_environment
        workspace = tmp_path / "ws-dedup"
        workspace.mkdir()
        memory_dir = make_memory_recall_directory(fake_home, workspace)
        (memory_dir / "user-x.md").write_text(
            "# user-x\n\n- 2026-05-17: pnpm is preferred\n"
        )
        path_set_hash = memory_recall.hash_recall_path_set(
            [str((memory_dir / "user-x.md").resolve())]
        )
        self._seed_recent_state("session-dedup", [path_set_hash])
        result = invoke_memory_recall_hook(
            {
                "cwd": str(workspace),
                "tool_input": {"command": "pnpm install"},
                "session_id": "session-dedup",
            }
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_same_path_set_emits_when_not_already_injected(
        self,
        tmp_path,
        isolated_memory_recall_environment,
        invoke_memory_recall_hook,
        make_memory_recall_directory,
    ):
        fake_home, _ = isolated_memory_recall_environment
        workspace = tmp_path / "ws-dedup-control"
        workspace.mkdir()
        memory_dir = make_memory_recall_directory(fake_home, workspace)
        (memory_dir / "user-x.md").write_text(
            "# user-x\n\n- 2026-05-17: pnpm is preferred\n"
        )
        self._seed_recent_state("session-dedup-control", [])
        result = invoke_memory_recall_hook(
            {
                "cwd": str(workspace),
                "tool_input": {"command": "pnpm install"},
                "session_id": "session-dedup-control",
            }
        )
        assert result.returncode == 0
        assert result.stdout != ""
