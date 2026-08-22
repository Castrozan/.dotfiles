import json

from hook_dispatch_test_support import (
    HookHandler,
    context_handler,
    decision_handler,
    emit_context_injection,
    emit_stop_decision,
    run_handlers,
    system_message_handler,
)


def test_emit_context_injection_writes_combined_payload(capsys):
    outcome = run_handlers({}, [context_handler("alpha"), context_handler("beta")])
    emit_context_injection("SessionStart", outcome)
    payload = json.loads(capsys.readouterr().out)
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert payload["hookSpecificOutput"]["additionalContext"] == "alpha\n\nbeta"


def test_emit_context_injection_is_silent_when_no_context(capsys):
    outcome = run_handlers({}, [HookHandler(handle=lambda hook_input: None)])
    emit_context_injection("SessionStart", outcome)
    assert capsys.readouterr().out.strip() == ""


def test_emit_stop_decision_only_prints_on_block(capsys):
    emit_stop_decision(run_handlers({}, [context_handler("noise")]))
    assert capsys.readouterr().out.strip() == ""
    emit_stop_decision(run_handlers({}, [decision_handler("block", "stop reason")]))
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"decision": "block", "reason": "stop reason"}


def test_emit_stop_decision_emits_system_message_without_block(capsys):
    emit_stop_decision(run_handlers({}, [system_message_handler("advisory only")]))
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"continue": True, "systemMessage": "advisory only"}


def test_emit_stop_decision_unions_system_message_and_block(capsys):
    outcome = run_handlers(
        {},
        [system_message_handler("human advisory"), decision_handler("block", "shape")],
    )
    emit_stop_decision(outcome)
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "continue": True,
        "systemMessage": "human advisory",
        "decision": "block",
        "reason": "shape",
    }
