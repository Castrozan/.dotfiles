from hook_bridge_test_support import invoke_hook_bridge, only_dispatcher_record


def test_compaction_hook_adds_dispatcher_context_to_the_compaction_prompt(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {
            "hookSpecificOutput": {
                "additionalContext": "Re-read the active deep-work tracker."
            }
        },
        "experimental.session.compacting",
        {"sessionID": "ses-5"},
        {"context": [], "prompt": None},
    )

    assert "error" not in result
    assert result["hookOutput"]["context"] == ["Re-read the active deep-work tracker."]
    record = only_dispatcher_record(records)
    assert record == {
        "dispatcher": "session-start-dispatcher.py",
        "payload": {
            "hook_event_name": "SessionStart",
            "session_id": "ses-5",
            "source": "compact",
            "cwd": "/workspace/project",
        },
    }
