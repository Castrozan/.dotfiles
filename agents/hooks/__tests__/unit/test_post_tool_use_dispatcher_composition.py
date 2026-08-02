import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hook_module_loader import import_hyphenated_hook_module

post_tool_use_dispatcher = import_hyphenated_hook_module("post-tool-use-dispatcher")

import auto_format_handler  # noqa: E402
import line_count_limit_guard_handler  # noqa: E402
import nix_rebuild_trigger_handler  # noqa: E402
import record_edited_source_file_handler  # noqa: E402
import record_skill_invocation_handler  # noqa: E402


def handlers_by_handle_function():
    return {
        handler.handle: handler
        for handler in post_tool_use_dispatcher.POST_TOOL_USE_HANDLERS
    }


def test_skill_matched_handler_records_skill_invocations():
    handlers = handlers_by_handle_function()
    assert handlers[record_skill_invocation_handler.handle].tool_matcher == "Skill"


def test_edit_or_write_matched_handlers_carry_the_edit_write_matcher():
    handlers = handlers_by_handle_function()
    for edit_or_write_handler_module in (
        auto_format_handler,
        record_edited_source_file_handler,
        nix_rebuild_trigger_handler,
        line_count_limit_guard_handler,
    ):
        assert (
            handlers[edit_or_write_handler_module.handle].tool_matcher == "Edit|Write"
        )


def test_auto_format_runs_before_record_edited_and_line_count():
    ordered_handle_functions = [
        handler.handle for handler in post_tool_use_dispatcher.POST_TOOL_USE_HANDLERS
    ]
    assert ordered_handle_functions.index(
        auto_format_handler.handle
    ) < ordered_handle_functions.index(record_edited_source_file_handler.handle)
    assert ordered_handle_functions.index(
        auto_format_handler.handle
    ) < ordered_handle_functions.index(line_count_limit_guard_handler.handle)
