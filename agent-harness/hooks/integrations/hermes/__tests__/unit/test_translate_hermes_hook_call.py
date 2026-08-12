import json

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


def test_an_event_the_shared_dispatchers_do_not_serve_is_dropped():
    assert translator.dispatcher_payload({"hook_event_name": "pre_llm_call"}) is None


def test_a_tool_without_a_canonical_name_keeps_its_own():
    payload = translator.dispatcher_payload(
        {"hook_event_name": "post_tool_call", "tool_name": "browser", "cwd": "/tmp"}
    )

    assert payload["hook_event_name"] == "PostToolUse"
    assert payload["tool_name"] == "browser"
    assert payload["tool_input"] == {}


def test_a_pre_tool_use_denial_becomes_a_hermes_block():
    response = translator.hermes_response(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "git add -A is prohibited",
                }
            }
        )
    )

    assert response == {"decision": "block", "reason": "git add -A is prohibited"}


def test_a_post_tool_use_block_becomes_a_hermes_block():
    response = translator.hermes_response(
        json.dumps({"decision": "block", "reason": "the turn review refused this"})
    )

    assert response == {
        "decision": "block",
        "reason": "the turn review refused this",
    }


def test_an_allowing_dispatcher_answers_nothing_at_all():
    assert translator.hermes_response("") is None
    assert translator.hermes_response("{}") is None
    assert (
        translator.hermes_response(
            json.dumps({"hookSpecificOutput": {"permissionDecision": "allow"}})
        )
        is None
    )
