from hook_bridge_test_support import invoke_hook_bridge, invoke_hook_bridge_sequence


def prompt(session_id, text):
    return {
        "hookName": "session.prompt",
        "event": {"sessionID": session_id, "prompt": {"text": text}},
    }


def test_session_start_injects_context_once_per_session(tmp_path):
    results, records = invoke_hook_bridge_sequence(
        tmp_path,
        {"hookSpecificOutput": {"additionalContext": "SESSION CONTEXT"}},
        [prompt("ses-1", "first"), prompt("ses-1", "second"), prompt("ses-2", "other")],
    )
    assert results[0]["event"]["prompt"]["text"] == "first\n\nSESSION CONTEXT"
    assert results[1]["event"]["prompt"]["text"] == "second"
    assert [item["payload"]["session_id"] for item in records] == ["ses-1", "ses-2"]
    assert all(item["payload"]["source"] == "startup" for item in records)


def test_failed_startup_does_not_block_and_can_retry(tmp_path):
    results, records = invoke_hook_bridge_sequence(
        tmp_path, "invalid JSON", [prompt("ses-1", "first"), prompt("ses-1", "second")]
    )
    assert all("error" not in result for result in results)
    assert len(records) == 2
    assert results[0]["event"]["prompt"]["text"] == "first"


def test_compaction_injects_recovery_into_model_system_context(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {"hookSpecificOutput": {"additionalContext": "Read the active tracker."}},
        "session.compaction",
        {"sessionID": "ses-1", "system": [{"type": "text", "text": "Summarize"}]},
    )
    assert result["event"]["system"] == [
        {"type": "text", "text": "Summarize"},
        {"type": "text", "text": "Read the active tracker."},
    ]
    assert records[0]["payload"]["source"] == "compact"
