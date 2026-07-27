from hook_dispatch_test_support import (
    HookHandler,
    context_handler,
    decision_handler,
    run_handlers,
)


def raising_handler(exception_message="simulated handler defect"):
    def handle(hook_input):
        raise RuntimeError(exception_message)

    return HookHandler(handle=handle)


def test_a_raising_handler_does_not_suppress_a_later_security_decision():
    outcome = run_handlers(
        {"tool_name": "Bash", "tool_input": {"command": "git add -A"}},
        [raising_handler(), decision_handler("deny", "blocked by the guard")],
    )
    assert outcome.decision == "deny"
    assert outcome.reason == "blocked by the guard"


def test_a_raising_handler_does_not_suppress_earlier_handlers():
    outcome = run_handlers(
        {"tool_name": "Bash", "tool_input": {}},
        [context_handler("first fragment"), raising_handler()],
    )
    assert "first fragment" in outcome.combined_additional_context


def test_a_raising_handler_is_surfaced_rather_than_swallowed_silently():
    outcome = run_handlers(
        {"tool_name": "Bash", "tool_input": {}},
        [raising_handler("boom"), context_handler("still ran")],
    )
    assert "still ran" in outcome.combined_additional_context
    assert outcome.combined_system_message


def test_every_remaining_handler_runs_when_several_raise():
    outcome = run_handlers(
        {"tool_name": "Bash", "tool_input": {}},
        [
            raising_handler("first defect"),
            context_handler("survivor one"),
            raising_handler("second defect"),
            context_handler("survivor two"),
        ],
    )
    assert "survivor one" in outcome.combined_additional_context
    assert "survivor two" in outcome.combined_additional_context
