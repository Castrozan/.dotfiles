import json

from hook_dispatch_test_support import (
    HookHandler,
    block_and_system_message_handler,
    context_and_system_message_handler,
    context_handler,
    decision_handler,
    deny_with_system_message_handler,
    emit_post_tool_use_outcome,
    emit_pretooluse_decision,
    run_handlers,
    system_message_handler,
    updated_input_handler,
)


def test_emit_post_tool_use_outcome_is_silent_when_empty(capsys):
    emit_post_tool_use_outcome(
        run_handlers({}, [HookHandler(handle=lambda hook_input: None)])
    )
    assert capsys.readouterr().out.strip() == ""


def test_emit_post_tool_use_outcome_injects_additional_context(capsys):
    emit_post_tool_use_outcome(run_handlers({}, [context_handler("ctx")]))
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "ctx",
        },
        "continue": True,
    }


def test_emit_post_tool_use_outcome_emits_system_message_only(capsys):
    emit_post_tool_use_outcome(run_handlers({}, [system_message_handler("advisory")]))
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"systemMessage": "advisory", "continue": True}


def test_emit_post_tool_use_outcome_unions_context_and_system_message(capsys):
    emit_post_tool_use_outcome(
        run_handlers({}, [context_and_system_message_handler("rebuild")])
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "systemMessage": "rebuild",
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "rebuild",
        },
        "continue": True,
    }


def test_emit_post_tool_use_outcome_unions_block_and_system_message(capsys):
    emit_post_tool_use_outcome(
        run_handlers({}, [block_and_system_message_handler("too long", "BLOCKED")])
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "systemMessage": "BLOCKED",
        "decision": "block",
        "reason": "too long",
        "continue": True,
    }


def test_emit_pretooluse_decision_is_silent_when_empty(capsys):
    emit_pretooluse_decision(
        run_handlers({}, [HookHandler(handle=lambda hook_input: None)])
    )
    assert capsys.readouterr().out.strip() == ""


def test_emit_pretooluse_decision_injects_additional_context_without_decision(capsys):
    emit_pretooluse_decision(run_handlers({}, [context_handler("Recall: @a @b")]))
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": "Recall: @a @b",
        },
        "continue": True,
    }


def test_emit_pretooluse_decision_unions_deny_and_system_message(capsys):
    emit_pretooluse_decision(
        run_handlers(
            {}, [deny_with_system_message_handler("blocked reason", "BLOCKED")]
        )
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "systemMessage": "BLOCKED",
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "blocked reason",
        },
        "continue": True,
    }


def test_emit_pretooluse_decision_carries_allow_with_updated_input(capsys):
    emit_pretooluse_decision(
        run_handlers({}, [updated_input_handler({"command": "cd /x && ls"})])
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "updatedInput": {"command": "cd /x && ls"},
        },
        "continue": True,
    }


def test_emit_pretooluse_decision_deny_wins_but_updated_input_survives(capsys):
    outcome = run_handlers(
        {},
        [
            updated_input_handler({"command": "cd /x && ls"}),
            decision_handler("deny", "blocked"),
        ],
    )
    emit_pretooluse_decision(outcome)
    payload = json.loads(capsys.readouterr().out)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert payload["hookSpecificOutput"]["permissionDecisionReason"] == "blocked"
    assert payload["hookSpecificOutput"]["updatedInput"] == {"command": "cd /x && ls"}
    assert payload["continue"] is True
