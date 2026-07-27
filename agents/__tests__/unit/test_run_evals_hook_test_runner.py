from run_evals_hook_test_runner import (
    HOOK_SCRIPT_SEARCH_ROOT,
    hook_blocked,
    hook_event_name_for_script,
    hook_message,
    interpret_hook_result,
    synthesize_hook_event,
)


def test_exit_code_two_is_a_block():
    assert hook_blocked(2, None) is True


def test_clean_exit_without_a_deny_is_not_a_block():
    assert hook_blocked(0, None) is False
    assert hook_blocked(0, {"continue": True, "systemMessage": "note"}) is False


def test_stdout_json_signals_a_block_three_ways():
    assert hook_blocked(0, {"continue": False}) is True
    assert hook_blocked(0, {"decision": "block"}) is True
    assert (
        hook_blocked(0, {"hookSpecificOutput": {"permissionDecision": "deny"}}) is True
    )


def test_message_gathers_stderr_and_the_json_fields():
    message = hook_message(
        stdout="",
        stderr="use fxtwitter",
        stdout_json=None,
    )
    assert "use fxtwitter" in message

    message = hook_message(
        stdout='{"systemMessage": "MANDATORY rebuild"}',
        stderr="",
        stdout_json={
            "systemMessage": "MANDATORY rebuild",
            "hookSpecificOutput": {"additionalContext": "stage and commit"},
        },
    )
    assert "MANDATORY rebuild" in message
    assert "stage and commit" in message


def test_non_blocking_message_hook_passes_its_assertions():
    failures = interpret_hook_result(
        returncode=0,
        stdout='{"continue": true, "systemMessage": "MANDATORY: test.nix changed"}',
        stderr="",
        assertions={"hook_blocks": False, "message_contains": "MANDATORY"},
    )
    assert failures == []


def test_blocking_stderr_hook_passes_its_assertions():
    failures = interpret_hook_result(
        returncode=2,
        stdout="",
        stderr="Use the fxtwitter API instead",
        assertions={"hook_blocks": True, "message_contains": "fxtwitter"},
    )
    assert failures == []


def test_wrong_block_outcome_is_reported():
    failures = interpret_hook_result(
        returncode=0,
        stdout="",
        stderr="",
        assertions={"hook_blocks": True},
    )
    assert len(failures) == 1
    assert "hook_blocks" in failures[0]


def test_missing_expected_message_is_reported():
    failures = interpret_hook_result(
        returncode=2,
        stdout="",
        stderr="some other reason",
        assertions={"hook_blocks": True, "message_contains": "fxtwitter"},
    )
    assert len(failures) == 1
    assert "fxtwitter" in failures[0]


def test_event_synthesis_moves_trigger_fields_into_tool_input():
    event = synthesize_hook_event(
        {"tool": "Edit", "file_path": "test.nix"}, "PreToolUse"
    )
    assert event["tool_name"] == "Edit"
    assert event["tool_input"] == {"file_path": "test.nix"}


def test_event_synthesis_carries_the_event_name_it_was_given():
    event = synthesize_hook_event({"tool": "Edit"}, "PostToolUse")
    assert event["hook_event_name"] == "PostToolUse"


class TestTheEventNameIsDerivedFromTheHookRatherThanAssumed:
    def test_a_post_tool_use_hook_is_given_a_post_tool_use_event(self):
        script = (
            HOOK_SCRIPT_SEARCH_ROOT / "post-tool-use" / "post-tool-use-dispatcher.py"
        )
        assert hook_event_name_for_script(script) == "PostToolUse"

    def test_a_pre_tool_use_hook_is_given_a_pre_tool_use_event(self):
        script = HOOK_SCRIPT_SEARCH_ROOT / "pre-tool-use" / "pre-tool-use-dispatcher.py"
        assert hook_event_name_for_script(script) == "PreToolUse"

    def test_a_multi_word_event_directory_becomes_one_pascal_case_name(self):
        script = HOOK_SCRIPT_SEARCH_ROOT / "user-prompt-submit" / "anything.py"
        assert hook_event_name_for_script(script) == "UserPromptSubmit"

    def test_a_hook_nested_under_its_own_folder_still_reports_the_event(self):
        script = (
            HOOK_SCRIPT_SEARCH_ROOT
            / "pre-tool-use"
            / "prohibited-command-guard"
            / "prohibited_command_guard_handler.py"
        )
        assert hook_event_name_for_script(script) == "PreToolUse"
