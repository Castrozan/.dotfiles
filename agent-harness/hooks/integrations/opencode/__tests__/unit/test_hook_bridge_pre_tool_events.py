from hook_bridge_test_support import invoke_hook_bridge, only_dispatcher_record


def test_pre_tool_hook_denies_a_normalized_bash_command(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {
            "hookSpecificOutput": {
                "permissionDecision": "deny",
                "permissionDecisionReason": "git add . is prohibited",
            }
        },
        "tool.execute.before",
        {"tool": "bash", "sessionID": "ses-1", "callID": "call-1"},
        {"args": {"command": "git add ."}},
    )

    assert result["error"] == "git add . is prohibited"
    record = only_dispatcher_record(records)
    assert record == {
        "dispatcher": "pre-tool-use-dispatcher.py",
        "payload": {
            "hook_event_name": "PreToolUse",
            "session_id": "ses-1",
            "cwd": "/workspace/project",
            "tool_name": "Bash",
            "tool_input": {"command": "git add ."},
        },
    }


def test_pre_tool_hook_applies_updated_input_with_opencode_argument_names(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {
            "hookSpecificOutput": {
                "permissionDecision": "allow",
                "updatedInput": {
                    "file_path": "src/example.py",
                    "old_string": "before",
                    "new_string": "after",
                },
            }
        },
        "tool.execute.before",
        {"tool": "edit", "sessionID": "ses-2", "callID": "call-2"},
        {
            "args": {
                "filePath": "src/example.py",
                "oldString": "before",
                "newString": "after",
            }
        },
    )

    assert "error" not in result
    assert result["hookOutput"]["args"] == {
        "filePath": "src/example.py",
        "oldString": "before",
        "newString": "after",
    }
    assert result["originalToolArgumentsWereRetained"]
    record = only_dispatcher_record(records)
    assert record["payload"]["tool_name"] == "Edit"
    assert record["payload"]["tool_input"] == {
        "file_path": "src/example.py",
        "old_string": "before",
        "new_string": "after",
    }


def test_pre_tool_hook_translates_the_opencode_skill_name(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {
            "hookSpecificOutput": {
                "permissionDecision": "deny",
                "permissionDecisionReason": "blocked skill",
            }
        },
        "tool.execute.before",
        {"tool": "skill", "sessionID": "ses-6", "callID": "call-6"},
        {"args": {"name": "claude-api"}},
    )

    assert result["error"] == "blocked skill"
    assert only_dispatcher_record(records)["payload"]["tool_input"] == {
        "skill": "claude-api"
    }


def test_apply_patch_hook_passes_raw_patch_text_to_shared_handlers(tmp_path):
    patch_text = "*** Update File: module.py\n@@\n-value = 1\n+value = 2\n"
    result, records = invoke_hook_bridge(
        tmp_path,
        {
            "hookSpecificOutput": {
                "permissionDecision": "deny",
                "permissionDecisionReason": "patch blocked",
            }
        },
        "tool.execute.before",
        {"tool": "apply_patch", "sessionID": "ses-10", "callID": "call-10"},
        {"args": {"patchText": patch_text}},
    )

    assert result["error"] == "patch blocked"
    record = only_dispatcher_record(records)
    assert record["payload"]["tool_name"] == "apply_patch"
    assert record["payload"]["tool_input"] == patch_text


def test_pre_tool_hook_rejects_non_object_dispatcher_output(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        [],
        "tool.execute.before",
        {"tool": "bash", "sessionID": "ses-11", "callID": "call-11"},
        {"args": {"command": "git add ."}},
    )

    assert (
        result["error"]
        == "OpenCode pre-tool-use-dispatcher.py hook returned invalid JSON"
    )
    assert only_dispatcher_record(records)["payload"]["tool_name"] == "Bash"
