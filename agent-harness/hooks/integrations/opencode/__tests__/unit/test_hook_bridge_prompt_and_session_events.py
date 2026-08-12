from hook_bridge_test_support import (
    invoke_hook_bridge,
    invoke_hook_bridge_sequence,
    only_dispatcher_record,
)


def chat_message_call(session_id, prompt_text):
    return {
        "hookName": "chat.message",
        "hookInput": {"sessionID": session_id},
        "hookOutput": {"parts": [{"type": "text", "text": prompt_text}]},
    }


def test_first_message_of_a_session_injects_the_session_start_context(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {"hookSpecificOutput": {"additionalContext": "SESSION CONTEXT: branch main"}},
        "chat.message",
        {"sessionID": "ses-9"},
        {"parts": [{"type": "text", "text": "fix the build"}]},
    )

    assert "error" not in result
    assert result["hookOutput"]["parts"][0]["text"] == (
        "fix the build\n\nSESSION CONTEXT: branch main"
    )
    record = only_dispatcher_record(records)
    assert record == {
        "dispatcher": "session-start-dispatcher.py",
        "payload": {
            "hook_event_name": "SessionStart",
            "session_id": "ses-9",
            "source": "startup",
            "cwd": "/workspace/project",
        },
    }


def test_session_start_fires_once_per_session_not_once_per_message(tmp_path):
    results, records = invoke_hook_bridge_sequence(
        tmp_path,
        {"hookSpecificOutput": {"additionalContext": "SESSION CONTEXT: branch main"}},
        [
            chat_message_call("ses-9", "first"),
            chat_message_call("ses-9", "second"),
            chat_message_call("ses-10", "another session"),
        ],
    )

    assert [record["payload"]["session_id"] for record in records] == [
        "ses-9",
        "ses-10",
    ]
    assert results[1]["hookOutput"]["parts"][0]["text"] == "second"


def test_a_failing_session_start_dispatcher_never_blocks_the_message(tmp_path):
    result, _ = invoke_hook_bridge(
        tmp_path,
        "not json at all",
        "chat.message",
        {"sessionID": "ses-11"},
        {"parts": [{"type": "text", "text": "carry on"}]},
    )

    assert "error" not in result
    assert result["hookOutput"]["parts"][0]["text"] == "carry on"


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
