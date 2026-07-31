import sys
from pathlib import Path

import pytest

HOOKS_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HOOKS_ROOT / "common"))

from hook_dispatch import (  # noqa: E402
    CLAUDE_SURFACE,
    CODEX_SURFACE,
    HandlerResult,
    HookHandler,
    handler_matches_tool,
    handler_runs_on_surface,
    requested_hook_surface,
    run_handlers,
)

DISPATCHERS_BY_REGISTRY_NAME = {
    "PRE_TOOL_USE_HANDLERS": "pre-tool-use-dispatcher",
    "POST_TOOL_USE_HANDLERS": "post-tool-use-dispatcher",
    "STOP_HANDLERS": "stop-dispatcher",
    "SESSION_START_HANDLERS": "session-start-dispatcher",
}

HANDLERS_REQUIRED_ON_THE_CODEX_SURFACE = {
    "PRE_TOOL_USE_HANDLERS": {
        "prohibited_command_guard_handler",
        "prohibited_words_guard_handler",
        "agent_instruction_file_authoring_router_handler",
        "worktree_location_guard_handler",
    },
    "POST_TOOL_USE_HANDLERS": {
        "auto_format_handler",
        "nix_rebuild_trigger_handler",
        "record_edited_source_file_handler",
        "line_count_limit_guard_handler",
    },
    "STOP_HANDLERS": {"lint_turn_review_handler"},
    "SESSION_START_HANDLERS": {
        "compaction_context_recovery_handler",
        "herdr_agent_session_report_handler",
    },
}

HANDLERS_THAT_MUST_STAY_OFF_THE_CODEX_SURFACE = {
    "PRE_TOOL_USE_HANDLERS": {
        "background_bash_anti_pattern_validator_handler",
        "codex_sandbox_downgrade_guard_handler",
        "workspace_directory_injector_handler",
    },
    "STOP_HANDLERS": {"end_of_turn_format_guard_handler"},
    "SESSION_START_HANDLERS": {"session_context_handler"},
}


def handler_module_names_on_surface(registry_name, surface):
    from hook_module_loader import import_hyphenated_hook_module

    dispatcher = import_hyphenated_hook_module(
        DISPATCHERS_BY_REGISTRY_NAME[registry_name]
    )
    return {
        handler.handle.__module__
        for handler in getattr(dispatcher, registry_name)
        if handler_runs_on_surface(handler, surface)
    }


@pytest.mark.parametrize(
    "registry_name", sorted(HANDLERS_REQUIRED_ON_THE_CODEX_SURFACE)
)
def test_codex_surface_keeps_the_handlers_it_registered_before_the_fold(registry_name):
    running_on_codex = handler_module_names_on_surface(registry_name, CODEX_SURFACE)
    assert HANDLERS_REQUIRED_ON_THE_CODEX_SURFACE[registry_name] <= running_on_codex


@pytest.mark.parametrize(
    "registry_name", sorted(HANDLERS_THAT_MUST_STAY_OFF_THE_CODEX_SURFACE)
)
def test_claude_only_handlers_stay_off_the_codex_surface(registry_name):
    running_on_codex = handler_module_names_on_surface(registry_name, CODEX_SURFACE)
    running_on_claude = handler_module_names_on_surface(registry_name, CLAUDE_SURFACE)
    claude_only = HANDLERS_THAT_MUST_STAY_OFF_THE_CODEX_SURFACE[registry_name]
    assert claude_only.isdisjoint(running_on_codex)
    assert claude_only <= running_on_claude


def test_codex_session_start_does_not_scan_deep_work_workspaces():
    running_on_codex = handler_module_names_on_surface(
        "SESSION_START_HANDLERS", CODEX_SURFACE
    )
    assert "deep_work_context_handler" not in running_on_codex


def test_run_handlers_skips_handlers_that_do_not_declare_the_surface():
    def always_reports(_hook_input):
        return HandlerResult(system_message="ran")

    outcome = run_handlers(
        {"tool_name": "Bash"},
        [HookHandler(handle=always_reports, surfaces=(CLAUDE_SURFACE,))],
        CODEX_SURFACE,
    )
    assert outcome.combined_system_message == ""


def test_codex_apply_patch_matches_the_claude_write_matcher():
    write_handler = HookHandler(handle=lambda _: None, tool_matcher="Edit|Write")
    assert handler_matches_tool(write_handler, "apply_patch")
    assert handler_matches_tool(write_handler, "Edit")
    assert not handler_matches_tool(write_handler, "Bash")


def test_requested_hook_surface_defaults_to_claude(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["pre-tool-use-dispatcher.py"])
    assert requested_hook_surface() == CLAUDE_SURFACE
    monkeypatch.setattr(sys, "argv", ["pre-tool-use-dispatcher.py", "--surface=codex"])
    assert requested_hook_surface() == CODEX_SURFACE
