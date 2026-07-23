import concurrent.futures

import memory_recall


def build_concurrent_payloads(workspace, session_id):
    return [
        {
            "cwd": str(workspace),
            "tool_input": {"command": "pnpm install"},
            "session_id": session_id,
        },
        {
            "cwd": str(workspace),
            "tool_input": {"command": "docker compose up"},
            "session_id": session_id,
        },
    ]


def seed_two_distinct_memories(memory_directory):
    (memory_directory / "packaging.md").write_text(
        "# packaging\n\n- 2026-05-17: pnpm is the preferred installer\n"
    )
    (memory_directory / "containers.md").write_text(
        "# containers\n\n- 2026-05-17: docker compose runs the stack\n"
    )


class TestConcurrentToolCallsShareOneDebounceWindow:
    def test_parallel_hook_invocations_inject_recall_only_once(
        self,
        tmp_path,
        isolated_memory_recall_environment,
        invoke_memory_recall_hook,
        make_memory_recall_directory,
    ):
        fake_home, _ = isolated_memory_recall_environment
        workspace = tmp_path / "ws-concurrent"
        workspace.mkdir()
        seed_two_distinct_memories(make_memory_recall_directory(fake_home, workspace))
        payloads = build_concurrent_payloads(workspace, "session-concurrent")
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(payloads)) as pool:
            results = list(pool.map(invoke_memory_recall_hook, payloads))
        assert all(result.returncode == 0 for result in results)
        assert sum(1 for result in results if result.stdout != "") == 1

    def test_parallel_hook_invocations_record_one_injection_in_state(
        self,
        tmp_path,
        isolated_memory_recall_environment,
        invoke_memory_recall_hook,
        make_memory_recall_directory,
    ):
        fake_home, _ = isolated_memory_recall_environment
        workspace = tmp_path / "ws-concurrent-state"
        workspace.mkdir()
        seed_two_distinct_memories(make_memory_recall_directory(fake_home, workspace))
        payloads = build_concurrent_payloads(workspace, "session-concurrent-state")
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(payloads)) as pool:
            list(pool.map(invoke_memory_recall_hook, payloads))
        state = memory_recall.load_debounce_state(
            memory_recall.debounce_state_path_for_session("session-concurrent-state")
        )
        assert state["recall_event_count"] == 1
        assert state["suppressed_event_count_by_reason"] == {
            memory_recall.SUPPRESSION_REASON_DEBOUNCE: 1
        }

    def test_single_invocation_still_injects(
        self,
        tmp_path,
        isolated_memory_recall_environment,
        invoke_memory_recall_hook,
        make_memory_recall_directory,
    ):
        fake_home, _ = isolated_memory_recall_environment
        workspace = tmp_path / "ws-concurrent-control"
        workspace.mkdir()
        seed_two_distinct_memories(make_memory_recall_directory(fake_home, workspace))
        result = invoke_memory_recall_hook(
            build_concurrent_payloads(workspace, "session-concurrent-control")[0]
        )
        assert result.returncode == 0
        assert result.stdout != ""
