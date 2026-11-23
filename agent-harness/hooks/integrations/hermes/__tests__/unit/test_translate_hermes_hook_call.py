import json

import pytest

import translate_hermes_hook_call as translator


def test_a_terminal_call_becomes_a_bash_pre_tool_use_payload():
    payload = translator.dispatcher_payload(
        {
            "hook_event_name": "pre_tool_call",
            "tool_name": "terminal",
            "tool_input": {"command": "git add -A"},
            "session_id": "sess_abc",
            "cwd": "/workspace/project",
        }
    )

    assert payload == {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "git add -A"},
        "session_id": "sess_abc",
        "cwd": "/workspace/project",
    }


def test_a_tool_without_a_canonical_name_keeps_its_own():
    payload = translator.dispatcher_payload(
        {"hook_event_name": "post_tool_call", "tool_name": "browser", "cwd": "/tmp"}
    )

    assert payload["hook_event_name"] == "PostToolUse"
    assert payload["tool_name"] == "browser"
    assert payload["tool_input"] == {}


def test_a_post_tool_use_block_becomes_a_hermes_block():
    response = translator.hermes_response(
        json.dumps({"decision": "block", "reason": "the turn review refused this"}),
        "terminal",
    )

    assert response == {
        "decision": "block",
        "reason": "the turn review refused this",
    }


def test_an_allowing_dispatcher_answers_nothing_at_all():
    assert translator.hermes_response("", "terminal") is None
    assert translator.hermes_response("{}", "terminal") is None
    assert (
        translator.hermes_response(
            json.dumps({"hookSpecificOutput": {"permissionDecision": "allow"}}),
            "terminal",
        )
        is None
    )


@pytest.mark.parametrize("decision", ["deny", "block"])
def test_permission_denial_wins_over_accidental_updated_input(decision):
    response = translator.hermes_response(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "permissionDecision": decision,
                    "permissionDecisionReason": "forbidden",
                    "updatedInput": {"command": "rewritten"},
                }
            }
        ),
        "terminal",
    )
    assert response == {"decision": "block", "reason": "forbidden"}


@pytest.mark.parametrize("decision", ["deny", "block"])
def test_top_level_denial_wins_over_allowed_updated_input(decision):
    response = translator.hermes_response(
        json.dumps(
            {
                "decision": decision,
                "reason": "forbidden",
                "hookSpecificOutput": {
                    "permissionDecision": "allow",
                    "updatedInput": {"command": "rewritten"},
                },
            }
        ),
        "terminal",
    )
    assert response == {"decision": "block", "reason": "forbidden"}


def test_unknown_tool_updated_input_preserves_opaque_fields():
    updated_input = {"file_path": "opaque", "path": "another", "values": [1, 2]}
    response = translator.hermes_response(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "permissionDecision": "allow",
                    "updatedInput": updated_input,
                }
            }
        ),
        "unknown_tool",
    )
    assert response == {"action": "modify", "args": updated_input}
