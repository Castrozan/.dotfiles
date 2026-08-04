import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hook_module_loader import import_hyphenated_hook_module

post_tool_use_dispatcher = import_hyphenated_hook_module("post-tool-use-dispatcher")


def handlers_by_module_name():
    return {
        handler.handler_module_name: handler
        for handler in post_tool_use_dispatcher.POST_TOOL_USE_HANDLERS
    }


def ordered_handler_module_names():
    return [
        handler.handler_module_name
        for handler in post_tool_use_dispatcher.POST_TOOL_USE_HANDLERS
    ]


def test_skill_matched_handler_records_skill_invocations():
    handlers = handlers_by_module_name()
    assert handlers["record_skill_invocation_handler"].tool_matcher == "Skill"


def test_edit_or_write_matched_handlers_carry_the_edit_write_matcher():
    handlers = handlers_by_module_name()
    for edit_or_write_handler_module_name in (
        "auto_format_handler",
        "record_edited_source_file_handler",
        "nix_rebuild_trigger_handler",
        "line_count_limit_guard_handler",
    ):
        assert handlers[edit_or_write_handler_module_name].tool_matcher == "Edit|Write"


def test_auto_format_runs_before_record_edited_and_line_count():
    ordered = ordered_handler_module_names()
    assert ordered.index("auto_format_handler") < ordered.index(
        "record_edited_source_file_handler"
    )
    assert ordered.index("auto_format_handler") < ordered.index(
        "line_count_limit_guard_handler"
    )


def test_no_handler_loads_unless_an_edit_write_or_skill_call_selects_it():
    for handler in post_tool_use_dispatcher.POST_TOOL_USE_HANDLERS:
        assert handler.tool_matcher, (
            "every PostToolUse handler carries a matcher, which is what lets the "
            "registration narrow to Skill|Edit|Write and skip the interpreter "
            "entirely on a Read or a Bash; a matcher-less handler here would force "
            f"the registration back to .*: {handler.handler_module_name}"
        )
        assert handler.handle is None, (
            "a handler resolved at table construction time has already paid its "
            f"import: {handler.handler_module_name}"
        )
