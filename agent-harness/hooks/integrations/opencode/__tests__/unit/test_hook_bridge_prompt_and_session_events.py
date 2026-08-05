from hook_bridge_test_support import invoke_hook_bridge, only_dispatcher_record


def test_user_prompt_hook_adds_dispatcher_context_to_the_prompt_text(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {
            "hookSpecificOutput": {
                "additionalContext": "Use the enforced reply template."
            }
        },
        "chat.message",
        {"sessionID": "ses-4"},
        {
            "message": {"id": "msg-4"},
            "parts": [
                {
                    "id": "prt-4",
                    "sessionID": "ses-4",
                    "messageID": "msg-4",
                    "type": "text",
                    "text": "Continue",
                }
            ],
        },
    )

    assert "error" not in result
    assert result["hookOutput"]["parts"][0]["text"] == (
        "Continue\n\nUse the enforced reply template."
    )
    record = only_dispatcher_record(records)
    assert record == {
        "dispatcher": "user-prompt-submit-dispatcher.py",
        "payload": {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "ses-4",
            "cwd": "/workspace/project",
        },
    }


def test_file_only_prompt_defers_context_injection_until_a_text_prompt(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {
            "hookSpecificOutput": {
                "additionalContext": "Use the enforced reply template."
            }
        },
        "chat.message",
        {"sessionID": "ses-9"},
        {
            "message": {"id": "msg-9"},
            "parts": [
                {
                    "id": "prt-9",
                    "sessionID": "ses-9",
                    "messageID": "msg-9",
                    "type": "file",
                    "mime": "image/png",
                    "url": "file:///tmp/example.png",
                }
            ],
        },
    )

    assert "error" not in result
    assert records == []


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
