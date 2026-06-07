import importlib.util
import pathlib
import sys


def _load_tmux_module():
    module_path = (
        pathlib.Path(__file__).resolve().parent.parent.parent / "heartbeat" / "tmux.py"
    )
    module_spec = importlib.util.spec_from_file_location("heartbeat_tmux", module_path)
    module = importlib.util.module_from_spec(module_spec)
    sys.modules["heartbeat_tmux"] = module
    module_spec.loader.exec_module(module)
    return module


tmux_module = _load_tmux_module()


def test_paste_buffer_name_is_unique_per_target():
    name_for_first_agent = tmux_module.build_paste_buffer_name("clawde:jenny")
    name_for_second_agent = tmux_module.build_paste_buffer_name("esfinge:esfinge")
    assert name_for_first_agent != name_for_second_agent, (
        "two agents pasting concurrently must use distinct tmux buffer names; "
        "a shared name lets one agent's delete-buffer wipe another's before it pastes"
    )


def test_paste_buffer_name_has_no_tmux_target_separator():
    buffer_name = tmux_module.build_paste_buffer_name("esfinge:esfinge")
    assert ":" not in buffer_name, (
        "the ':' that separates session from window in a tmux target must not leak "
        "into the buffer name"
    )


def test_pane_at_repl_prompt_detects_bare_marker():
    assert tmux_module.pane_is_at_claude_repl_prompt("some output\n❯\n")
    assert tmux_module.pane_is_at_claude_repl_prompt("prefixed line ❯")


def test_pane_with_empty_prompt_and_trailing_space_is_idle():
    assert tmux_module.pane_is_at_claude_repl_prompt("some output\n❯ \n")


def test_pane_with_autosuggestion_ghost_is_idle():
    pane_with_history_ghost = (
        "✻ Cooked for 39s\n"
        "──── steward ──\n"
        "❯\xa0Leave the submodule, end the tick\n"
        "────\n"
    )
    assert tmux_module.pane_is_at_claude_repl_prompt(pane_with_history_ghost)


def test_pane_with_real_typed_input_is_not_idle():
    pane_with_pending_input = "some output\n❯ git status\n"
    assert not tmux_module.pane_is_at_claude_repl_prompt(pane_with_pending_input)


def test_pane_at_onboarding_is_not_treated_as_idle_prompt():
    onboarding_pane = "Select login method\n❯ 1. Claude account with subscription"
    assert not tmux_module.pane_is_at_claude_repl_prompt(onboarding_pane)
