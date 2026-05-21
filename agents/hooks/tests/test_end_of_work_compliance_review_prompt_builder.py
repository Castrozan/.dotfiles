import pytest

import end_of_work_compliance_review as hook


@pytest.fixture(autouse=True)
def _apply_compliance_review_test_isolation(
    reset_session_id_prefix_between_tests, isolate_persistent_log_file
):
    return isolate_persistent_log_file


class TestSummarizeToolCallForPrompt:
    def test_extracts_file_path(self):
        result = hook.summarize_tool_call_for_prompt(
            {"name": "Read", "input": {"file_path": "/tmp/x"}}
        )
        assert result == "Read(file_path=/tmp/x)"

    def test_extracts_command_truncated(self):
        long_command = "echo " + "x" * 500
        result = hook.summarize_tool_call_for_prompt(
            {"name": "Bash", "input": {"command": long_command}}
        )
        assert result.startswith("Bash(command=")
        assert len(result) < len(long_command) + 50

    def test_falls_back_to_compact_json(self):
        result = hook.summarize_tool_call_for_prompt(
            {"name": "Custom", "input": {"unknown_field": "value"}}
        )
        assert "Custom(" in result
        assert "unknown_field" in result


class TestHasAnyFileMutatingToolCall:
    def test_true_when_edit_present(self):
        assert hook.has_any_file_mutating_tool_call(
            [{"name": "Read"}, {"name": "Edit"}]
        )

    def test_true_when_write_present(self):
        assert hook.has_any_file_mutating_tool_call([{"name": "Write"}])

    def test_false_when_only_reads(self):
        assert not hook.has_any_file_mutating_tool_call(
            [{"name": "Read"}, {"name": "Grep"}, {"name": "Glob"}]
        )

    def test_false_on_empty_list(self):
        assert not hook.has_any_file_mutating_tool_call([])


class TestBuildReviewUserPrompt:
    def test_includes_all_provided_sections(self):
        context = {
            "prior_user_prompts": ["earlier ask"],
            "prior_assistant_messages": ["earlier reply"],
            "current_user_prompts": ["fix the bug in foo.py"],
            "ordered_tool_calls": [
                {"id": "call_1", "name": "Read", "input": {"file_path": "foo.py"}},
                {"id": "call_2", "name": "Edit", "input": {"file_path": "foo.py"}},
            ],
            "tool_results_by_use_id": {"call_1": "contents of foo.py"},
            "assistant_text": "Done.",
        }
        workspace_docs = {"CLAUDE.md": "rules"}
        git_diff = "diff content"

        prompt = hook.build_review_user_prompt(context, workspace_docs, git_diff)

        assert "Earlier in this session (user)" in prompt
        assert "earlier ask" in prompt
        assert "Earlier in this session (agent text)" in prompt
        assert "earlier reply" in prompt
        assert "User's request for this turn" in prompt
        assert "fix the bug in foo.py" in prompt
        assert "Tool calls (in order, with truncated results)" in prompt
        assert "1. Read" in prompt
        assert "2. Edit" in prompt
        assert "-> result: contents of foo.py" in prompt
        assert "Agent's final response" in prompt
        assert "Done." in prompt
        assert "Workspace policy docs" in prompt
        assert "CLAUDE.md" in prompt
        assert "Git diff" in prompt
        assert "diff content" in prompt
        assert "Your task" in prompt
        assert "FAIL" in prompt

    def test_skips_absent_sections(self):
        prompt = hook.build_review_user_prompt({}, {}, "")
        assert "Earlier in this session" not in prompt
        assert "Tool calls (in order" not in prompt
        assert "Workspace policy docs" not in prompt
        assert "Git diff" not in prompt
        assert "Your task" in prompt

    def test_indicates_tool_call_overflow(self):
        many_calls = [
            {"name": "Read", "input": {"file_path": f"file{index}.py"}}
            for index in range(hook.MAX_TOOL_CALLS_IN_PROMPT + 5)
        ]
        prompt = hook.build_review_user_prompt(
            {"ordered_tool_calls": many_calls}, {}, ""
        )
        assert "... and 5 more" in prompt
