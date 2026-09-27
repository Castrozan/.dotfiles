from hook_bridge_test_support import invoke_hook_bridge_sequence


def event(kind, **data):
    return {
        "hookName": "event",
        "event": {"type": kind, "data": {"sessionID": "ses-1", **data}},
    }


def prompt():
    return {
        "hookName": "session.prompt",
        "event": {"sessionID": "ses-1", "prompt": {"text": "summarize"}},
    }


def reply(message_id, text):
    return event(
        "session.text.ended", assistantMessageID=message_id, ordinal=0, text=text
    )


def test_completion_reviews_the_reply_and_queues_one_synthetic_correction(tmp_path):
    results, records = invoke_hook_bridge_sequence(
        tmp_path,
        {"decision": "block", "reason": "Rewrite."},
        [
            prompt(),
            reply("msg-1", "Sure, done."),
            event("session.execution.succeeded"),
            event("session.execution.succeeded"),
            reply("msg-2", "Done."),
            event("session.execution.succeeded"),
        ],
    )
    stops = [
        record for record in records if record["dispatcher"] == "stop-dispatcher.py"
    ]
    assert len(stops) == 2
    assert stops[0]["payload"]["reply_text"] == "Sure, done."
    assert stops[0]["payload"]["user_request_text"] == "summarize"
    assert stops[1]["payload"]["stop_hook_active"] is True
    assert results[-1]["syntheticCalls"] == [
        {"sessionID": "ses-1", "text": "Rewrite.", "delivery": "queue", "resume": True}
    ]


def test_unrelated_failed_and_deleted_sessions_do_not_trigger_reply_review(tmp_path):
    _, records = invoke_hook_bridge_sequence(
        tmp_path,
        {},
        [
            event("session.execution.succeeded"),
            prompt(),
            reply("msg-1", "Partial"),
            event("session.execution.failed"),
            event("session.deleted"),
            event("session.execution.succeeded"),
        ],
    )
    assert all(record["dispatcher"] != "stop-dispatcher.py" for record in records)


def test_new_user_turn_gets_its_own_correction_allowance(tmp_path):
    results, _ = invoke_hook_bridge_sequence(
        tmp_path,
        {"decision": "block", "reason": "Rewrite."},
        [
            prompt(),
            reply("msg-1", "First"),
            event("session.execution.succeeded"),
            prompt(),
            reply("msg-2", "Second"),
            event("session.execution.succeeded"),
        ],
    )
    assert len(results[-1]["syntheticCalls"]) == 2
