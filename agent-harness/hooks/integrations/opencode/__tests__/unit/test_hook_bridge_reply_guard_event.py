from hook_bridge_test_support import invoke_hook_bridge, invoke_hook_bridge_sequence


SESSION_MESSAGES = [
    {
        "info": {"id": "msg-user", "role": "user"},
        "parts": [{"type": "text", "text": "summarize the result"}],
    },
    {
        "info": {"id": "msg-assistant", "role": "assistant"},
        "parts": [{"type": "text", "text": "Sure, here it is."}],
    },
]


def idle_hook_call():
    return {
        "hookName": "event",
        "hookInput": {
            "event": {
                "type": "session.idle",
                "properties": {"sessionID": "ses-5"},
            }
        },
        "hookOutput": {},
    }


def test_session_idle_reviews_the_final_human_facing_reply(tmp_path):
    reason = "Remove the sycophancy opener and answer directly."
    result, records = invoke_hook_bridge(
        tmp_path,
        {"decision": "block", "reason": reason},
        "event",
        idle_hook_call()["hookInput"],
        {},
        session_messages=SESSION_MESSAGES,
    )

    assert "error" not in result
    assert records == [
        {
            "dispatcher": "stop-dispatcher.py",
            "payload": {
                "hook_event_name": "Stop",
                "session_id": "ses-5",
                "cwd": "/workspace/project",
                "user_request_text": "summarize the result",
                "reply_text": "Sure, here it is.",
            },
        }
    ]
    assert result["promptAsyncCalls"] == [
        {
            "path": {"id": "ses-5"},
            "query": {"directory": "/workspace/project"},
            "body": {"system": reason, "parts": []},
        }
    ]


def test_session_idle_allows_only_one_format_correction(tmp_path):
    corrected_messages = [
        *SESSION_MESSAGES,
        {
            "info": {"id": "msg-correction", "role": "assistant"},
            "parts": [{"type": "text", "text": "The result is complete."}],
        },
    ]
    correction_idle = idle_hook_call()
    correction_idle["sessionMessages"] = corrected_messages
    results, records = invoke_hook_bridge_sequence(
        tmp_path,
        {"decision": "block", "reason": "Rewrite the reply."},
        [idle_hook_call(), idle_hook_call(), correction_idle],
        session_messages=SESSION_MESSAGES,
    )

    assert len(records) == 1
    assert len(results[-1]["promptAsyncCalls"]) == 1
