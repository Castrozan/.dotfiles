from hook_bridge_test_support import invoke_hook_bridge


def tool_event(status="completed", content="Wrote config.nix"):
    return {
        "tool": "write",
        "sessionID": "ses-3",
        "input": {"path": "config.nix", "content": "{}"},
        "status": status,
        "result": {"content": content},
    }


def test_post_tool_hook_adds_guidance_to_the_native_result(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path, {"systemMessage": "Run rebuild."}, "tool.execute.after", tool_event()
    )
    assert result["event"]["result"]["content"] == "Wrote config.nix\n\nRun rebuild."
    assert records[0]["payload"]["tool_input"] == {
        "file_path": "config.nix",
        "content": "{}",
    }


def test_post_tool_hook_preserves_structured_content(tmp_path):
    original = [{"type": "text", "text": "output"}]
    result, _ = invoke_hook_bridge(
        tmp_path,
        {"systemMessage": "Run rebuild."},
        "tool.execute.after",
        tool_event(content=original),
    )
    assert result["event"]["result"]["content"] == original + [
        {"type": "text", "text": "Run rebuild."}
    ]


def test_post_tool_hook_rejects_a_blocking_decision(tmp_path):
    result, _ = invoke_hook_bridge(
        tmp_path,
        {"decision": "block", "reason": "Split the file."},
        "tool.execute.after",
        tool_event(),
    )
    assert result["error"] == "Split the file."


def test_failed_tools_do_not_report_successful_file_changes(tmp_path):
    _, records = invoke_hook_bridge(
        tmp_path, {}, "tool.execute.after", tool_event(status="error")
    )
    assert records == []


def test_post_tool_hook_never_reviews_the_final_reply(tmp_path):
    _, records = invoke_hook_bridge(tmp_path, {}, "tool.execute.after", tool_event())
    assert all(record["dispatcher"] != "stop-dispatcher.py" for record in records)
