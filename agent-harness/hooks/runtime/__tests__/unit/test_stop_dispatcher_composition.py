import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hook_module_loader import import_hyphenated_hook_module

stop_dispatcher = import_hyphenated_hook_module("stop-dispatcher")


def test_stop_dispatcher_composes_both_guard_handlers():
    handlers_by_module_name = {
        handler.handler_module_name: handler
        for handler in stop_dispatcher.STOP_HANDLERS
    }
    assert "lint_turn_review_handler" in handlers_by_module_name
    assert "end_of_turn_format_guard_handler" in handlers_by_module_name
    assert handlers_by_module_name["lint_turn_review_handler"].tool_matcher is None
