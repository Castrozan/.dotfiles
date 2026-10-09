import json

from native_opencode_server import native_server


def verify_native_tool_outcomes(executable, environment, workspace, model, record):
    original_marker = workspace / "original-command"
    rewritten_marker = workspace / "rewritten-command"
    responses = {
        "pre-tool-use-dispatcher.py": {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "updatedInput": {"command": f"touch {rewritten_marker}"},
            }
        },
        "post-tool-use-dispatcher.py": {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "NATIVE_POST_TOOL_CONTEXT",
            }
        },
    }
    with native_server(
        executable,
        environment | {"OPENCODE_HOOK_RESPONSES": json.dumps(responses)},
        workspace,
    ) as server:
        session = server.request(
            "/api/session",
            {
                "title": "Native tool outcomes",
                "agent": "software-engineer",
                "model": {"providerID": "acceptance", "id": "fixture"},
                "location": {"directory": str(workspace)},
            },
        )["data"]["id"]
        server.request(
            f"/api/session/{session}/prompt",
            {
                "text": json.dumps(
                    {
                        "tool": "shell",
                        "input": {"command": f"touch {original_marker}"},
                    }
                )
            },
        )
        server.request(f"/api/experimental/session/{session}/wait", {}, method="POST")
        assert rewritten_marker.exists()
        assert not original_marker.exists()
        assert any(
            "NATIVE_POST_TOOL_CONTEXT" in json.dumps(request)
            for request in model.requests
        ), model.requests
        payloads = json.loads(record.read_text())
        post_tool_payload = next(
            item["payload"]
            for item in payloads
            if item["dispatcher"] == "post-tool-use-dispatcher.py"
        )
        assert post_tool_payload["tool_name"] == "Bash"
        assert post_tool_payload["tool_input"]["command"] == f"touch {rewritten_marker}"
        assert "tool_response" in post_tool_payload
    record.unlink()
    model.requests.clear()
