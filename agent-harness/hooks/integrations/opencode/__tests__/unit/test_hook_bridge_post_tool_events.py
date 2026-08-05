from hook_bridge_test_support import invoke_hook_bridge


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
        {
            "tool": "write",
            "sessionID": "ses-3",
            "callID": "call-3",
            "args": {"filePath": "config.nix", "content": "{}"},
        },
        {"title": "Write", "output": "Wrote config.nix", "metadata": {}},
        dispatcher_responses={"stop-dispatcher.py": {}},
    )

    assert "error" not in result
    assert result["hookOutput"]["output"] == (
        "Wrote config.nix\n\nMANDATORY: config.nix changed.\n\n"
        "Run rebuild before responding."
    )
    assert [record["dispatcher"] for record in records] == [
        "post-tool-use-dispatcher.py",
        "stop-dispatcher.py",
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
        {
            "tool": "write",
            "sessionID": "ses-7",
            "callID": "call-7",
            "args": {"filePath": "large.py", "content": ""},
        },
        {"title": "Write", "output": "Wrote large.py", "metadata": {}},
        dispatcher_responses={"stop-dispatcher.py": {}},
    )

    assert result["error"] == "Split the file before continuing."
    assert [record["dispatcher"] for record in records] == [
        "post-tool-use-dispatcher.py",
        "stop-dispatcher.py",
    ]


def test_post_tool_block_outranks_a_failing_turn_review_dispatcher(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {"decision": "block", "reason": "Split the file before continuing."},
        "tool.execute.after",
        {
            "tool": "write",
            "sessionID": "ses-12",
            "callID": "call-12",
            "args": {"filePath": "large.py", "content": ""},
        },
        {"title": "Write", "output": "Wrote large.py", "metadata": {}},
        dispatcher_responses={"stop-dispatcher.py": "not-json"},
    )

    assert result["error"] == "Split the file before continuing."
    assert [record["dispatcher"] for record in records] == [
        "post-tool-use-dispatcher.py",
        "stop-dispatcher.py",
    ]


def test_post_tool_hook_surfaces_a_failing_turn_review_dispatcher(tmp_path):
    result, _ = invoke_hook_bridge(
        tmp_path,
        {},
        "tool.execute.after",
        {
            "tool": "write",
            "sessionID": "ses-13",
            "callID": "call-13",
            "args": {"filePath": "module.py", "content": "value = 1\n"},
        },
        {"title": "Write", "output": "Wrote module.py", "metadata": {}},
        dispatcher_responses={"stop-dispatcher.py": "not-json"},
    )

    assert result["error"] == "OpenCode stop-dispatcher.py hook returned invalid JSON"


def test_post_tool_hook_runs_the_turn_review_dispatcher(tmp_path):
    result, records = invoke_hook_bridge(
        tmp_path,
        {"systemMessage": "MANDATORY: config.nix changed."},
        "tool.execute.after",
        {
            "tool": "write",
            "sessionID": "ses-8",
            "callID": "call-8",
            "args": {"filePath": "module.py", "content": "value = 1\n"},
        },
        {"title": "Write", "output": "Wrote module.py", "metadata": {}},
        dispatcher_responses={
            "stop-dispatcher.py": {"systemMessage": "Run ruff before pushing."}
        },
    )

    assert "error" not in result
    assert result["hookOutput"]["output"] == (
        "Wrote module.py\n\nMANDATORY: config.nix changed.\n\nRun ruff before pushing."
    )
    assert [record["dispatcher"] for record in records] == [
        "post-tool-use-dispatcher.py",
        "stop-dispatcher.py",
    ]
