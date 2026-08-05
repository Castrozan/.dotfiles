import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hook_module_loader import import_hyphenated_hook_module

pre_tool_use_dispatcher = import_hyphenated_hook_module("pre-tool-use-dispatcher")


def handlers_by_module_name():
    return {
        handler.handler_module_name: handler
        for handler in pre_tool_use_dispatcher.PRE_TOOL_USE_HANDLERS
    }


def ordered_handler_module_names():
    return [
        handler.handler_module_name
        for handler in pre_tool_use_dispatcher.PRE_TOOL_USE_HANDLERS
    ]


def test_codex_sandbox_downgrade_guard_matches_only_the_codex_launch_tool():
    handlers = handlers_by_module_name()
    assert (
        handlers["codex_sandbox_downgrade_guard_handler"].tool_matcher
        == "mcp__codex__codex"
    )


def test_prohibited_command_and_words_guards_run_on_every_tool():
    handlers = handlers_by_module_name()
    assert handlers["prohibited_command_guard_handler"].tool_matcher is None
    assert handlers["prohibited_words_guard_handler"].tool_matcher is None


def test_tool_specific_handlers_carry_their_matchers():
    handlers = handlers_by_module_name()
    assert handlers["workspace_directory_injector_handler"].tool_matcher == "Bash"
    assert (
        handlers["background_bash_anti_pattern_validator_handler"].tool_matcher
        == "Bash"
    )
    assert handlers["blocked_skill_invocation_guard_handler"].tool_matcher == "Skill"
    assert handlers["url_to_skill_router_handler"].tool_matcher == "WebFetch"
    assert (
        handlers["monitor_streaming_pattern_validator_handler"].tool_matcher
        == "Monitor"
    )
    assert (
        handlers["agent_instruction_file_authoring_router_handler"].tool_matcher
        == "Write|Edit"
    )
    assert (
        handlers["documentation_authoring_router_handler"].tool_matcher == "Write|Edit"
    )


def test_prohibited_command_guard_runs_before_the_tool_specific_handlers():
    ordered = ordered_handler_module_names()
    assert ordered.index("prohibited_command_guard_handler") < ordered.index(
        "workspace_directory_injector_handler"
    )


def test_every_handler_is_named_by_module_so_the_import_stays_lazy():
    for handler in pre_tool_use_dispatcher.PRE_TOOL_USE_HANDLERS:
        assert handler.handler_module_name, (
            "PreToolUse runs on every tool call, so a handler bound as an already "
            "imported function reintroduces the eager import the lazy table exists "
            "to avoid; name the module and let run_handlers import it on a match"
        )
        assert handler.handle is None, (
            "a handler resolved at table construction time has already paid its "
            f"import: {handler.handler_module_name}"
        )
