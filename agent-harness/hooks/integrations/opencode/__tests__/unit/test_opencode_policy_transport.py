import importlib.util
import json
import subprocess
import sys
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
            {"path": "x", "oldString": "a", "newString": "b"},
            "Edit",
            {"file_path": "x", "old_string": "a", "new_string": "b"},
        ),
        ("skill", {"id": "coding"}, "Skill", {"skill": "coding"}),
        (
            "subagent",
            {"agent": "explore", "prompt": "find"},
            "Agent",
            {"subagent_type": "explore", "prompt": "find"},
        ),
        ("patch", {"patchText": "patch"}, "apply_patch", "patch"),
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


def test_updated_input_uses_native_argument_names():
    decision = {
        "hookSpecificOutput": {"updatedInput": {"file_path": "x", "new_string": "b"}}
    }
    assert payload.native_output(decision)["hookSpecificOutput"]["updatedInput"] == {
        "path": "x",
        "newString": "b",
    }


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
