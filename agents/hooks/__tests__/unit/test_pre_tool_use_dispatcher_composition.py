import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hook_module_loader import import_hyphenated_hook_module

pre_tool_use_dispatcher = import_hyphenated_hook_module("pre-tool-use-dispatcher")

import agent_instruction_file_authoring_router_handler  # noqa: E402
import background_bash_anti_pattern_validator_handler  # noqa: E402
import blocked_skill_invocation_guard_handler  # noqa: E402
import codex_sandbox_downgrade_guard_handler  # noqa: E402
import documentation_authoring_router_handler  # noqa: E402
import monitor_streaming_pattern_validator_handler  # noqa: E402
import prohibited_command_guard_handler  # noqa: E402
import prohibited_words_guard_handler  # noqa: E402
import url_to_skill_router_handler  # noqa: E402
import workspace_directory_injector_handler  # noqa: E402


def handlers_by_handle_function():
    return {
        handler.handle: handler
        for handler in pre_tool_use_dispatcher.PRE_TOOL_USE_HANDLERS
    }


def test_codex_sandbox_downgrade_guard_matches_only_the_codex_launch_tool():
    handlers = handlers_by_handle_function()
    assert (
        handlers[codex_sandbox_downgrade_guard_handler.handle].tool_matcher
        == "mcp__codex__codex"
    )


def test_prohibited_command_and_words_guards_run_on_every_tool():
    handlers = handlers_by_handle_function()
    assert handlers[prohibited_command_guard_handler.handle].tool_matcher is None
    assert handlers[prohibited_words_guard_handler.handle].tool_matcher is None


def test_tool_specific_handlers_carry_their_matchers():
    handlers = handlers_by_handle_function()
    assert handlers[workspace_directory_injector_handler.handle].tool_matcher == "Bash"
    assert (
        handlers[background_bash_anti_pattern_validator_handler.handle].tool_matcher
        == "Bash"
    )
    assert (
        handlers[blocked_skill_invocation_guard_handler.handle].tool_matcher == "Skill"
    )
    assert handlers[url_to_skill_router_handler.handle].tool_matcher == "WebFetch"
    assert (
        handlers[monitor_streaming_pattern_validator_handler.handle].tool_matcher
        == "Monitor"
    )
    assert (
        handlers[agent_instruction_file_authoring_router_handler.handle].tool_matcher
        == "Write|Edit"
    )
    assert (
        handlers[documentation_authoring_router_handler.handle].tool_matcher
        == "Write|Edit"
    )


def test_prohibited_command_guard_runs_before_the_tool_specific_handlers():
    ordered_handle_functions = [
        handler.handle for handler in pre_tool_use_dispatcher.PRE_TOOL_USE_HANDLERS
    ]
    assert ordered_handle_functions.index(
        prohibited_command_guard_handler.handle
    ) < ordered_handle_functions.index(workspace_directory_injector_handler.handle)
