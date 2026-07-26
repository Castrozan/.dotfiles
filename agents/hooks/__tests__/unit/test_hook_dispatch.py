import json
import sys
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
HOOK_DISPATCH_MODULE_DIRECTORY = next(HOOKS_ROOT.rglob("hook_dispatch.py")).parent
if str(HOOK_DISPATCH_MODULE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(HOOK_DISPATCH_MODULE_DIRECTORY))

from hook_dispatch import (  # noqa: E402
    HandlerResult,
    HookHandler,
    emit_context_injection,
    emit_post_tool_use_outcome,
    emit_stop_decision,
    run_handlers,
)


def context_handler(text):
    return HookHandler(handle=lambda hook_input: HandlerResult(additional_context=text))


def decision_handler(decision, reason, tool_matcher=None):
    return HookHandler(
        handle=lambda hook_input: HandlerResult(decision=decision, reason=reason),
        tool_matcher=tool_matcher,
    )


def system_message_handler(text):
    return HookHandler(handle=lambda hook_input: HandlerResult(system_message=text))


def test_context_fragments_concatenate_in_registry_order():
    outcome = run_handlers({}, [context_handler("first"), context_handler("second")])
    assert outcome.combined_additional_context == "first\n\nsecond"


def test_abstaining_handler_returning_none_is_skipped():
    abstain = HookHandler(handle=lambda hook_input: None)
    outcome = run_handlers({}, [abstain, context_handler("only")])
    assert outcome.combined_additional_context == "only"
    assert outcome.decision is None


def test_tool_matcher_gates_which_handlers_run():
    bash_only = decision_handler("block", "bash reason", tool_matcher="Bash")
    outcome_other = run_handlers({"tool_name": "Edit"}, [bash_only])
    assert outcome_other.decision is None
    outcome_bash = run_handlers({"tool_name": "Bash"}, [bash_only])
    assert outcome_bash.decision == "block"


def test_stronger_decision_wins_regardless_of_order():
    handlers = [
        decision_handler("allow", "allowed"),
        decision_handler("deny", "denied"),
    ]
    outcome = run_handlers({}, handlers)
    assert outcome.decision == "deny"
    assert outcome.reason == "denied"


def test_first_handler_wins_a_tie_in_decision_strength():
    handlers = [decision_handler("block", "first"), decision_handler("deny", "second")]
    outcome = run_handlers({}, handlers)
    assert outcome.decision == "block"
    assert outcome.reason == "first"


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


def test_system_messages_combine_across_handlers_in_order():
    outcome = run_handlers(
        {}, [system_message_handler("first advisory"), system_message_handler("second")]
    )
    assert outcome.combined_system_message == "first advisory\n\nsecond"


def test_emit_stop_decision_emits_system_message_without_block(capsys):
    emit_stop_decision(run_handlers({}, [system_message_handler("advisory only")]))
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"continue": True, "systemMessage": "advisory only"}


def test_emit_stop_decision_unions_system_message_and_block(capsys):
    outcome = run_handlers(
        {},
        [system_message_handler("lint advisory"), decision_handler("block", "shape")],
    )
    emit_stop_decision(outcome)
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "continue": True,
        "systemMessage": "lint advisory",
        "decision": "block",
        "reason": "shape",
    }


def context_and_system_message_handler(text):
    return HookHandler(
        handle=lambda hook_input: HandlerResult(
            additional_context=text, system_message=text
        )
    )


def block_and_system_message_handler(reason, system_message):
    return HookHandler(
        handle=lambda hook_input: HandlerResult(
            decision="block", reason=reason, system_message=system_message
        )
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
