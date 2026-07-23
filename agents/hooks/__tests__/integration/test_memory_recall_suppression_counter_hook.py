import json
import time

import memory_recall


class TestHookRecordsSuppressionCounters:
    def test_budget_suppression_is_counted_in_state(
        self,
        tmp_path,
        isolated_memory_recall_environment,
        invoke_memory_recall_hook,
        make_memory_recall_directory,
    ):
        fake_home, _ = isolated_memory_recall_environment
        workspace = tmp_path / "ws-budget-counter"
        workspace.mkdir()
        memory_dir = make_memory_recall_directory(fake_home, workspace)
        (memory_dir / "user-x.md").write_text(
            "# user-x\n\n- 2026-05-17: pnpm is preferred\n"
        )
        session_id = "session-budget-counter"
        state_path = memory_recall.debounce_state_path_for_session(session_id)
        state_path.write_text(
            json.dumps(
                {"recall_event_count": memory_recall.SESSION_RECALL_EVENT_BUDGET}
            )
        )
        invoke_memory_recall_hook(
            {
                "cwd": str(workspace),
                "tool_input": {"command": "pnpm install"},
                "session_id": session_id,
            }
        )
        state = memory_recall.load_debounce_state(state_path)
        assert (
            state["suppressed_event_count_by_reason"][
                memory_recall.SUPPRESSION_REASON_BUDGET
            ]
            == 1
        )

    def test_dedup_suppression_records_count_and_characters(
        self,
        tmp_path,
        isolated_memory_recall_environment,
        invoke_memory_recall_hook,
        make_memory_recall_directory,
    ):
        fake_home, _ = isolated_memory_recall_environment
        workspace = tmp_path / "ws-dedup-counter"
        workspace.mkdir()
        memory_dir = make_memory_recall_directory(fake_home, workspace)
        (memory_dir / "user-x.md").write_text(
            "# user-x\n\n- 2026-05-17: pnpm is preferred\n"
        )
        session_id = "session-dedup-counter"
        path_set_hash = memory_recall.hash_recall_path_set(
            [str((memory_dir / "user-x.md").resolve())]
        )
        state_path = memory_recall.debounce_state_path_for_session(session_id)
        state_path.write_text(
            json.dumps(
                {
                    "last_fire_timestamp": time.time() - 100,
                    "last_keywords": ["unrelated-keyword"],
                    "injected_recall_path_set_hashes": [path_set_hash],
                }
            )
        )
        invoke_memory_recall_hook(
            {
                "cwd": str(workspace),
                "tool_input": {"command": "pnpm install"},
                "session_id": session_id,
            }
        )
        state = memory_recall.load_debounce_state(state_path)
        assert (
            state["suppressed_event_count_by_reason"][
                memory_recall.SUPPRESSION_REASON_DEDUP
            ]
            == 1
        )
        assert state["dedup_suppressed_character_total"] > 0
