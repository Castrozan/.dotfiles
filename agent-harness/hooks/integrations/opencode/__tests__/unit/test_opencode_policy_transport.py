import importlib.util
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest


TRANSPORT = Path(__file__).resolve().parents[2] / "policy-transport"
spec = importlib.util.spec_from_file_location(
    "opencode_payload", TRANSPORT / "opencode_payload.py"
)
payload = importlib.util.module_from_spec(spec)
spec.loader.exec_module(payload)


@pytest.mark.parametrize(
    ("native", "arguments", "canonical", "expected"),
    [
        ("shell", {"command": "true"}, "Bash", {"command": "true"}),
        (
            "write",
            {"path": "x", "content": "y"},
            "Write",
            {"file_path": "x", "content": "y"},
        ),
        (
            "edit",
            {"path": "x", "oldString": "a", "newString": "b", "replaceAll": True},
            "Edit",
            {
                "file_path": "x",
                "old_string": "a",
                "new_string": "b",
                "replace_all": True,
            },
        ),
        ("skill", {"id": "coding"}, "Skill", {"skill": "coding"}),
        (
            "subagent",
            {"agent": "explore", "prompt": "find", "sessionID": "child"},
            "Agent",
            {"subagent_type": "explore", "prompt": "find", "sessionID": "child"},
        ),
        ("patch", {"patchText": "patch"}, "apply_patch", "patch"),
        (
            "webfetch",
            {"url": "https://example.com"},
            "WebFetch",
            {"url": "https://example.com"},
        ),
    ],
)
def test_native_tools_preserve_the_existing_policy_contract(
    native, arguments, canonical, expected
):
    incoming = {
        "hook_event_name": "PreToolUse",
        "session_id": "owned",
        "tool_name": native,
        "tool_input": arguments,
    }
    assert payload.dispatcher_payload(incoming) == incoming | {
        "tool_name": canonical,
        "tool_input": expected,
    }
    assert incoming["tool_name"] == native
    assert incoming["tool_input"] == arguments


@pytest.mark.parametrize("tool_name", ["mcp__provider__lookup", "custom", "Read"])
def test_unknown_tool_arguments_preserve_opaque_provider_schema(tool_name):
    incoming = {
        "tool_name": tool_name,
        "tool_input": {
            "path": "opaque",
            "filePath": "provider-field",
            "newString": "provider-value",
            "sessionID": "provider-session",
            "nestedData": [{"path": "nested", "oldString": "provider-nested"}],
        },
    }
    original = deepcopy(incoming)

    assert payload.dispatcher_payload(incoming) == original
    assert incoming == original


@pytest.mark.parametrize(
    "tool_name", ["shell", "edit", "write", "skill", "subagent", "patch", "webfetch"]
)
def test_known_tool_arguments_preserve_unknown_fields_and_nested_values(tool_name):
    arguments = {
        "queryText": "opaque",
        "metadata": {"path": "nested", "newString": "opaque", "file_path": "opaque"},
        "values": [{"oldString": "opaque"}],
    }
    incoming = {"tool_name": tool_name, "tool_input": arguments}
    original = deepcopy(incoming)

    assert payload.dispatcher_payload(incoming)["tool_input"] == arguments
    assert incoming == original


def run_dispatcher(tmp_path, script, incoming):
    dispatcher = tmp_path / "dispatcher.py"
    dispatcher.write_text(script)
    return subprocess.run(
        [
            sys.executable,
            str(TRANSPORT / "dispatch.py"),
            str(dispatcher),
            "--surface=opencode",
        ],
        input=json.dumps(incoming),
        capture_output=True,
        text=True,
        timeout=5,
    )


def test_dispatcher_receives_normalized_input_and_returns_native_input(tmp_path):
    result = run_dispatcher(
        tmp_path,
        "import json,sys\npayload=json.load(sys.stdin)\n"
        'assert payload["tool_name"] == "Edit"\n'
        'assert sys.argv[1] == "--surface=opencode"\n'
        'print(json.dumps({"hookSpecificOutput":{"updatedInput":payload["tool_input"]}}))\n',
        {"tool_name": "edit", "tool_input": {"path": "x", "newString": "b"}},
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["hookSpecificOutput"]["updatedInput"] == {
        "path": "x",
        "newString": "b",
    }


@pytest.mark.parametrize(
    ("tool_name", "arguments"),
    [
        (
            "mcp__provider__lookup",
            {"path": "opaque", "newString": "opaque", "file_path": "provider"},
        ),
        (
            "shell",
            {"command": "true", "metadata": {"path": "opaque", "new_string": "opaque"}},
        ),
        ("edit", {"path": "x", "oldString": "a", "newString": "b", "replaceAll": True}),
        ("write", {"path": "x", "content": "data"}),
        ("skill", {"id": "coding"}),
        ("subagent", {"agent": "explore", "sessionID": "child", "prompt": "find"}),
        ("patch", {"patchText": "patch"}),
    ],
)
def test_dispatcher_roundtrip_preserves_the_native_tool_schema(
    tmp_path, tool_name, arguments
):
    result = run_dispatcher(
        tmp_path,
        "import json,sys\nreceived=json.load(sys.stdin)\n"
        'print(json.dumps({"continue": True, "systemMessage": "feedback", "hookSpecificOutput": {"permissionDecision": "allow", "additionalContext": "context", "updatedInput": received["tool_input"]}}))\n',
        {"tool_name": tool_name, "tool_input": arguments},
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "continue": True,
        "systemMessage": "feedback",
        "hookSpecificOutput": {
            "permissionDecision": "allow",
            "additionalContext": "context",
            "updatedInput": arguments,
        },
    }


@pytest.mark.parametrize(
    "script",
    [
        "raise SystemExit(2)",
        'print("{broken")',
        'print("[]")',
        'print("x" * (1024 * 1024 + 1))',
    ],
)
def test_dispatcher_failures_reach_the_generated_command_runtime(tmp_path, script):
    result = run_dispatcher(tmp_path, script, {})
    assert result.returncode != 0
    assert not result.stdout
