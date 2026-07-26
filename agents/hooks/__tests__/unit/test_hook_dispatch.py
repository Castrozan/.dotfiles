from hook_dispatch_test_support import (
    HookHandler,
    context_handler,
    decision_handler,
    run_handlers,
    system_message_handler,
)


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


def test_system_messages_combine_across_handlers_in_order():
    outcome = run_handlers(
        {}, [system_message_handler("first advisory"), system_message_handler("second")]
    )
    assert outcome.combined_system_message == "first advisory\n\nsecond"
