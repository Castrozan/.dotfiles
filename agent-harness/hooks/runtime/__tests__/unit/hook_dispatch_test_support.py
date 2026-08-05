import sys
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
HOOK_DISPATCH_MODULE_DIRECTORY = next(HOOKS_ROOT.rglob("hook_dispatch.py")).parent
if str(HOOK_DISPATCH_MODULE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(HOOK_DISPATCH_MODULE_DIRECTORY))

from hook_dispatch import (  # noqa: E402, F401
    HandlerResult,
    HookHandler,
    run_handlers,
)
from hook_event_output import (  # noqa: E402, F401
    emit_context_injection,
    emit_post_tool_use_outcome,
    emit_pretooluse_decision,
    emit_stop_decision,
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


def deny_with_system_message_handler(reason, system_message):
    return HookHandler(
        handle=lambda hook_input: HandlerResult(
            decision="deny", reason=reason, system_message=system_message
        )
    )


def updated_input_handler(updated_input, tool_matcher=None):
    return HookHandler(
        handle=lambda hook_input: HandlerResult(
            decision="allow", updated_input=updated_input
        ),
        tool_matcher=tool_matcher,
    )
