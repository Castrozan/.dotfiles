import json
import os
import subprocess
import sys

import pytest

import translate_hermes_hook_call as translator


@pytest.fixture
def invoke_bridge(tmp_path):
    dispatcher = tmp_path / "dispatcher"
    capture_path = tmp_path / "dispatch.json"
    response_path = tmp_path / "response.json"
    dispatcher.write_text(
        f"#!{sys.executable}\n"
        "import json\n"
        "import os\n"
        "from pathlib import Path\n"
        "import sys\n"
        "payload = json.load(sys.stdin)\n"
        "Path(os.environ['HERMES_TEST_CAPTURE_PATH']).write_text(json.dumps({\n"
        "    'name': sys.argv[1], 'payload': payload,\n"
        "}))\n"
        "print(Path(os.environ['HERMES_TEST_RESPONSE_PATH']).read_text())\n"
    )
    dispatcher.chmod(0o755)

    def invoke(payload, response):
        capture_path.unlink(missing_ok=True)
        response_path.write_text(json.dumps(response))
        environment = {
            **os.environ,
            "HERMES_TEST_CAPTURE_PATH": str(capture_path),
            "HERMES_TEST_RESPONSE_PATH": str(response_path),
        }
        completed = subprocess.run(
            [sys.executable, translator.__file__, str(dispatcher)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=environment,
            timeout=5.0,
        )
        assert completed.returncode == 0
        assert completed.stderr == ""
        native_response = json.loads(completed.stdout) if completed.stdout else None
        dispatched = (
            json.loads(capture_path.read_text()) if capture_path.exists() else None
        )
        return native_response, dispatched

    return invoke


def allowed_updated_input(tool_input):
    return {
        "hookSpecificOutput": {
            "permissionDecision": "allow",
            "updatedInput": tool_input,
        }
    }


@pytest.mark.parametrize(
    "native_tool, canonical_tool, native_input, canonical_input",
    [
        ("terminal", "Bash", {"command": "safe"}, {"command": "safe"}),
        ("write_file", "Write", {"path": "/tmp/file"}, {"file_path": "/tmp/file"}),
        ("patch", "Edit", {"path": "/tmp/file"}, {"file_path": "/tmp/file"}),
        (
            "patch",
            "apply_patch",
            {"mode": "patch", "patch": "*** Begin Patch\n*** End Patch\n"},
            {"mode": "patch", "patch_text": "*** Begin Patch\n*** End Patch\n"},
        ),
        ("browser", "browser", {"path": "opaque"}, {"path": "opaque"}),
    ],
)
def test_real_subprocess_round_trip_preserves_native_arguments(
    invoke_bridge, native_tool, canonical_tool, native_input, canonical_input
):
    opaque_input = {"nested": {"keep": [1, 2]}}
    response, dispatched = invoke_bridge(
        {
            "hook_event_name": "pre_tool_call",
            "tool_name": native_tool,
            "tool_input": {**native_input, **opaque_input},
            "extra": {"tool_call_id": "call-123"},
        },
        allowed_updated_input({**canonical_input, **opaque_input}),
    )
    assert response == {"action": "modify", "args": {**native_input, **opaque_input}}
    assert dispatched["name"] == "pre-tool-use-dispatcher.py"
    assert dispatched["payload"]["tool_name"] == canonical_tool
    assert dispatched["payload"]["tool_input"] == {**canonical_input, **opaque_input}
    assert dispatched["payload"]["tool_use_id"] == "call-123"


@pytest.mark.parametrize("tool_result", [None, {}, {"output": "done", "exit_code": 0}])
def test_post_tool_subprocess_forwards_native_result_and_correlation_id(
    invoke_bridge, tool_result
):
    response, dispatched = invoke_bridge(
        {
            "hook_event_name": "post_tool_call",
            "tool_name": "terminal",
            "tool_input": {"command": "safe"},
            "extra": {"result": tool_result, "tool_call_id": "call-456"},
        },
        {"hookSpecificOutput": {"additionalContext": "observer guidance"}},
    )
    assert response is None
    assert dispatched["name"] == "post-tool-use-dispatcher.py"
    assert dispatched["payload"]["hook_event_name"] == "PostToolUse"
    assert dispatched["payload"]["tool_response"] == tool_result
    assert dispatched["payload"]["tool_use_id"] == "call-456"


def test_unsupported_lifecycle_event_never_invokes_dispatcher(invoke_bridge):
    response, dispatched = invoke_bridge({"hook_event_name": "pre_llm_call"}, {})
    assert response is None
    assert dispatched is None


def test_subprocess_denial_keeps_existing_wire_shape_and_discards_rewrite(
    invoke_bridge,
):
    response, _ = invoke_bridge(
        {"hook_event_name": "pre_tool_call", "tool_name": "terminal"},
        {
            "hookSpecificOutput": {
                "permissionDecision": "deny",
                "permissionDecisionReason": "forbidden",
                "updatedInput": {"command": "rewritten"},
            }
        },
    )
    assert response == {"decision": "block", "reason": "forbidden"}


@pytest.mark.parametrize("extra", [None, [], "opaque"])
def test_invalid_extra_does_not_invent_post_tool_result(invoke_bridge, extra):
    response, dispatched = invoke_bridge(
        {"hook_event_name": "post_tool_call", "tool_name": "browser", "extra": extra},
        {},
    )
    assert response is None
    assert "tool_response" not in dispatched["payload"]
    assert "tool_use_id" not in dispatched["payload"]


def test_empty_dictionary_update_emits_native_modify_shape(invoke_bridge):
    response, _ = invoke_bridge(
        {"hook_event_name": "pre_tool_call", "tool_name": "terminal"},
        allowed_updated_input({}),
    )
    assert response == {"action": "modify", "args": {}}


def test_updated_input_without_explicit_allow_does_not_modify(invoke_bridge):
    response, _ = invoke_bridge(
        {"hook_event_name": "pre_tool_call", "tool_name": "terminal"},
        {"hookSpecificOutput": {"updatedInput": {"command": "rewritten"}}},
    )
    assert response is None
