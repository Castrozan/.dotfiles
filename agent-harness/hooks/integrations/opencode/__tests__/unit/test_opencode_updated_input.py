import importlib.util
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
    ("tool_name", "canonical", "native"),
    [
        (
            "shell",
            {"command": "true", "workdir": "x"},
            {"command": "true", "workdir": "x"},
        ),
        ("write", {"file_path": "x", "content": "y"}, {"path": "x", "content": "y"}),
        (
            "edit",
            {
                "file_path": "x",
                "old_string": "a",
                "new_string": "b",
                "replace_all": True,
            },
            {"path": "x", "oldString": "a", "newString": "b", "replaceAll": True},
        ),
        ("skill", {"skill": "coding"}, {"id": "coding"}),
        (
            "subagent",
            {"subagent_type": "explore", "prompt": "find", "sessionID": "child"},
            {"agent": "explore", "prompt": "find", "sessionID": "child"},
        ),
        ("patch", {"patch_text": "patch"}, {"patchText": "patch"}),
        ("patch", "patch", {"patchText": "patch"}),
        ("webfetch", {"url": "https://example.com"}, {"url": "https://example.com"}),
    ],
)
def test_updated_input_uses_only_the_original_tools_native_argument_names(
    tool_name, canonical, native
):
    decision = {
        "continue": True,
        "systemMessage": "retained feedback",
        "hookSpecificOutput": {
            "permissionDecision": "allow",
            "additionalContext": "retained context",
            "updatedInput": canonical,
        },
    }
    original = deepcopy(decision)

    assert payload.native_output(decision, tool_name) == decision | {
        "hookSpecificOutput": decision["hookSpecificOutput"] | {"updatedInput": native}
    }
    assert decision == original


@pytest.mark.parametrize("tool_name", ["mcp__provider__lookup", "custom", None])
def test_unknown_tool_rewrites_preserve_opaque_provider_schema(tool_name):
    decision = {
        "hookSpecificOutput": {
            "permissionDecision": "allow",
            "updatedInput": {
                "file_path": "provider-path",
                "new_string": "provider-value",
                "path": "native-provider-path",
                "newString": "native-provider-value",
                "nestedData": [{"file_path": "nested", "new_string": "nested-value"}],
            },
        }
    }
    original = deepcopy(decision)

    assert payload.native_output(decision, tool_name) == original
    assert decision == original


def test_local_rewrite_preserves_nested_values_and_unknown_top_level_fields():
    decision = {
        "hookSpecificOutput": {
            "updatedInput": {
                "file_path": "x",
                "skill": "opaque",
                "metadata": {"file_path": "nested", "new_string": "opaque"},
                "values": [{"old_string": "opaque"}],
            }
        }
    }
    original = deepcopy(decision)

    assert payload.native_output(decision, "edit")["hookSpecificOutput"][
        "updatedInput"
    ] == {
        "path": "x",
        "skill": "opaque",
        "metadata": {"file_path": "nested", "new_string": "opaque"},
        "values": [{"old_string": "opaque"}],
    }
    assert decision == original
