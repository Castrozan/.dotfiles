import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hook_module_loader import import_hyphenated_hook_module

stop_dispatcher = import_hyphenated_hook_module("stop-dispatcher")

import end_of_turn_format_guard_handler  # noqa: E402
import lint_turn_review_handler  # noqa: E402


def test_stop_dispatcher_composes_both_guard_handlers():
    handlers_by_function = {
        handler.handle: handler for handler in stop_dispatcher.STOP_HANDLERS
    }
    assert lint_turn_review_handler.handle in handlers_by_function
    assert end_of_turn_format_guard_handler.handle in handlers_by_function
    assert handlers_by_function[lint_turn_review_handler.handle].tool_matcher is None
