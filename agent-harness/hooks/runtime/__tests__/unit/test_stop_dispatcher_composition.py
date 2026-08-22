import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hook_module_loader import import_hyphenated_hook_module

stop_dispatcher = import_hyphenated_hook_module("stop-dispatcher")


def test_stop_dispatcher_composes_only_active_handlers():
    handler_module_names = {
        handler.handler_module_name for handler in stop_dispatcher.STOP_HANDLERS
    }
    assert handler_module_names == {
        "nix_rebuild_reminder_handler",
        "end_of_turn_format_guard_handler",
        "herdr_agent_session_report_handler",
    }
