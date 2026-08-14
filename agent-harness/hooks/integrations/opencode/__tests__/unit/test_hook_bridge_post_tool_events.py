from hook_bridge_test_support import invoke_hook_bridge


def tool_call(session_id="ses-3"):
    return {
        "tool": "write",
        "sessionID": session_id,
        "callID": "call-3",
        "args": {"filePath": "config.nix", "content": "{}"},
    }


def test_post_tool_hook_adds_dispatcher_guidance_to_tool_output(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {
            "systemMessage": "MANDATORY: config.nix changed.",
            "hookSpecificOutput": {
                "additionalContext": "Run rebuild before responding."
            },
        },
        "tool.execute.after",
        tool_call(),
        {"title": "Write", "output": "Wrote config.nix", "metadata": {}},
    )

    assert "error" not in result
    assert result["hookOutput"]["output"] == (
        "Wrote config.nix\n\nMANDATORY: config.nix changed.\n\n"
        "Run rebuild before responding."
    )
    assert [record["dispatcher"] for record in records] == [
        "post-tool-use-dispatcher.py"
    ]
    assert records[0]["payload"]["tool_name"] == "Write"
    assert records[0]["payload"]["tool_input"] == {
        "file_path": "config.nix",
        "content": "{}",
    }


def test_post_tool_hook_rejects_a_blocking_dispatcher_decision(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {"decision": "block", "reason": "Split the file before continuing."},
        "tool.execute.after",
        tool_call("ses-7"),
        {"title": "Write", "output": "Wrote config.nix", "metadata": {}},
    )

    assert result["error"] == "Split the file before continuing."
    assert [record["dispatcher"] for record in records] == [
        "post-tool-use-dispatcher.py"
    ]


def test_post_tool_hook_never_runs_the_final_reply_dispatcher(tmp_path):
    _, records = invoke_hook_bridge(
        tmp_path,
        {},
        "tool.execute.after",
        tool_call("ses-8"),
        {"title": "Write", "output": "Wrote config.nix", "metadata": {}},
    )

    assert "stop-dispatcher.py" not in [record["dispatcher"] for record in records]
