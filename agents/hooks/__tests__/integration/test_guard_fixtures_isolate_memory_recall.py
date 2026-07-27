import json


def test_guard_invocation_emits_nothing_when_the_debounce_window_is_open(
    invoke_prohibited_command_guard_hook, tmp_path, monkeypatch
):
    monkeypatch.setenv("MEMORY_RECALL_DEBOUNCE_STATE_DIRECTORY", str(tmp_path))
    result = invoke_prohibited_command_guard_hook(
        {
            "tool_name": "Bash",
            "tool_input": {"command": "herdr agent wait demo --status idle"},
            "session_id": "memory-recall-isolation-probe",
        }
    )

    assert result.returncode == 0
    assert result.stdout == "", (
        "a benign command leaked memory-recall context into the guard's output, so "
        "every guard test asserting empty stdout fails whenever the 30s debounce "
        f"window happens to be open: {result.stdout[:200]}"
    )


def test_a_real_denial_still_reaches_the_model(invoke_prohibited_command_guard_hook):
    result = invoke_prohibited_command_guard_hook(
        {
            "tool_name": "Bash",
            "tool_input": {"command": "git add -A"},
            "session_id": "memory-recall-isolation-probe",
        }
    )

    assert result.returncode == 0
    emitted = json.loads(result.stdout)
    assert emitted["hookSpecificOutput"]["permissionDecision"] == "deny"
