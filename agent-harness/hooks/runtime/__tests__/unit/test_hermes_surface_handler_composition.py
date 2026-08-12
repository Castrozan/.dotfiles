import sys
from pathlib import Path

import pytest

HOOKS_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HOOKS_ROOT / "common"))

from hook_dispatch import (  # noqa: E402
    CLAUDE_SURFACE,
    HERMES_SURFACE,
    requested_hook_surface,
)
from test_codex_surface_handler_composition import (  # noqa: E402
    handler_module_names_on_surface,
)

HANDLERS_REQUIRED_ON_THE_HERMES_SURFACE = {
    "PRE_TOOL_USE_HANDLERS": {
        "prohibited_command_guard_handler",
        "prohibited_words_guard_handler",
        "worktree_location_guard_handler",
        "agent_instruction_file_authoring_router_handler",
        "documentation_authoring_router_handler",
    },
    "POST_TOOL_USE_HANDLERS": {
        "auto_format_handler",
        "record_changed_nix_file_handler",
        "record_edited_source_file_handler",
        "line_count_limit_guard_handler",
    },
}

HANDLERS_THAT_MUST_STAY_OFF_THE_HERMES_SURFACE = {
    "PRE_TOOL_USE_HANDLERS": {
        "background_bash_anti_pattern_validator_handler",
        "blocked_skill_invocation_guard_handler",
        "codex_sandbox_downgrade_guard_handler",
        "monitor_streaming_pattern_validator_handler",
        "subagent_budget_guard_handler",
        "url_to_skill_router_handler",
        "workspace_directory_injector_handler",
    },
    "POST_TOOL_USE_HANDLERS": {"record_skill_invocation_handler"},
}


@pytest.mark.parametrize(
    "registry_name", sorted(HANDLERS_REQUIRED_ON_THE_HERMES_SURFACE)
)
def test_hermes_surface_runs_the_guards_a_shell_agent_can_honor(registry_name):
    running_on_hermes = handler_module_names_on_surface(registry_name, HERMES_SURFACE)
    assert HANDLERS_REQUIRED_ON_THE_HERMES_SURFACE[registry_name] <= running_on_hermes


@pytest.mark.parametrize(
    "registry_name", sorted(HANDLERS_THAT_MUST_STAY_OFF_THE_HERMES_SURFACE)
)
def test_hermes_surface_excludes_handlers_it_has_no_tool_for(registry_name):
    running_on_hermes = handler_module_names_on_surface(registry_name, HERMES_SURFACE)
    excluded = HANDLERS_THAT_MUST_STAY_OFF_THE_HERMES_SURFACE[registry_name]
    assert excluded.isdisjoint(running_on_hermes)
    assert excluded <= handler_module_names_on_surface(registry_name, CLAUDE_SURFACE)


def test_the_surface_flag_names_hermes(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["pre-tool-use-dispatcher.py", "--surface=hermes"])
    assert requested_hook_surface() == HERMES_SURFACE
