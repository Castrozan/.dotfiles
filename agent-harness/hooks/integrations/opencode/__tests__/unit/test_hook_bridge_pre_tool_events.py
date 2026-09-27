import pytest

from hook_bridge_test_support import invoke_hook_bridge, only_dispatcher_record


def test_pre_tool_hook_denies_a_normalized_shell_command(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {
            "hookSpecificOutput": {
                "permissionDecision": "deny",
                "permissionDecisionReason": "git add . is prohibited",
            }
        },
        "tool.execute.before",
        {"tool": "shell", "sessionID": "ses-1", "input": {"command": "git add ."}},
    )
    assert result["error"] == "git add . is prohibited"
    assert only_dispatcher_record(records)["payload"] == {
        "hook_event_name": "PreToolUse",
        "session_id": "ses-1",
        "cwd": "/workspace/project",
        "tool_name": "Bash",
        "tool_input": {"command": "git add ."},
    }


def test_pre_tool_hook_applies_updated_input_without_replacing_its_identity(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {
            "hookSpecificOutput": {
                "updatedInput": {
                    "file_path": "src/example.py",
                    "old_string": "before",
                    "new_string": "after",
                }
            }
        },
        "tool.execute.before",
        {
            "tool": "edit",
            "sessionID": "ses-2",
            "input": {
                "path": "src/example.py",
                "oldString": "before",
                "newString": "wrong",
            },
        },
    )
    assert "error" not in result
    assert result["event"]["input"] == {
        "path": "src/example.py",
        "oldString": "before",
        "newString": "after",
    }
    assert result["originalToolArgumentsWereRetained"]
    assert (
        only_dispatcher_record(records)["payload"]["tool_input"]["file_path"]
        == "src/example.py"
    )


@pytest.mark.parametrize(
    ("tool", "arguments", "canonical_name", "canonical_input"),
    [
        ("skill", {"id": "coding"}, "Skill", {"skill": "coding"}),
        (
            "subagent",
            {"agent": "explore", "prompt": "find it"},
            "Agent",
            {"subagent_type": "explore", "prompt": "find it"},
        ),
        (
            "patch",
            {"patchText": "*** Update File: module.py\n@@\n-x=1\n+x=2\n"},
            "apply_patch",
            "*** Update File: module.py\n@@\n-x=1\n+x=2\n",
        ),
    ],
)
def test_native_tool_inputs_reach_the_existing_dispatcher(
    tmp_path, tool, arguments, canonical_name, canonical_input
):
    _, records = invoke_hook_bridge(
        tmp_path,
        {},
        "tool.execute.before",
        {"tool": tool, "sessionID": "ses-3", "input": arguments},
    )
    payload = only_dispatcher_record(records)["payload"]
    assert payload["tool_name"] == canonical_name
    assert payload["tool_input"] == canonical_input


def test_pre_tool_hook_rejects_invalid_dispatcher_output(tmp_path):
    result, _ = invoke_hook_bridge(
        tmp_path,
        [],
        "tool.execute.before",
        {"tool": "shell", "sessionID": "ses-4", "input": {"command": "true"}},
    )
    assert (
        result["error"]
        == "OpenCode pre-tool-use-dispatcher.py hook returned invalid JSON"
    )
