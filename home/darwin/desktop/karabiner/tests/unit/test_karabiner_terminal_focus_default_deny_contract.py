from pathlib import Path

KARABINER_DIRECTORY = Path(__file__).parent.parent.parent
DEFAULT_DENY_GUARD_NIX_PATH = (
    KARABINER_DIRECTORY / "rules" / "non-terminal-frontmost-default-deny-guard.nix"
)
RULES_DEFAULT_NIX_PATH = KARABINER_DIRECTORY / "rules" / "default.nix"
HAMMERSPOON_TERMINAL_FOCUS_MODULE_PATH = (
    KARABINER_DIRECTORY.parent / "hammerspoon" / "karabiner_terminal_focus_variable.lua"
)
KICK_WHEN_CONFIG_CHANGED_NIX_PATH = (
    KARABINER_DIRECTORY
    / "config-deployment"
    / "kick-karabiner-user-agents-when-config-changed.nix"
)
COPY_KARABINER_JSON_SCRIPT_PATH = (
    KARABINER_DIRECTORY
    / "config-deployment"
    / "scripts"
    / "copy-karabiner-json-to-user-config.sh"
)

DEFAULT_DENY_VARIABLE_NAME = "non_terminal_application_is_frontmost"
CONFIG_CHANGED_SENTINEL_BASENAME = "karabiner-config-changed-since-last-kick"


def test_guard_file_is_the_single_source_of_truth_for_the_variable_name():
    guard_content = DEFAULT_DENY_GUARD_NIX_PATH.read_text()
    assert DEFAULT_DENY_VARIABLE_NAME in guard_content
    assert "defaultDenyCondition" in guard_content
    assert '"variable_if"' in guard_content
    assert "value = 1;" in guard_content


def test_rules_default_composes_exclude_terminals_from_the_guard():
    rules_default_content = RULES_DEFAULT_NIX_PATH.read_text()
    assert "non-terminal-frontmost-default-deny-guard.nix" in rules_default_content
    assert "defaultDenyCondition" in rules_default_content


def test_hammerspoon_sets_the_same_variable_name_the_guard_reads():
    assert (
        DEFAULT_DENY_VARIABLE_NAME in HAMMERSPOON_TERMINAL_FOCUS_MODULE_PATH.read_text()
    )


def test_hammerspoon_reports_zero_for_terminal_and_one_for_non_terminal():
    hammerspoon_content = HAMMERSPOON_TERMINAL_FOCUS_MODULE_PATH.read_text()
    assert "frontmostApplicationIsTerminal() and 0 or 1" in hammerspoon_content


def test_kick_runs_only_when_the_config_changed_sentinel_is_present():
    kick_content = KICK_WHEN_CONFIG_CHANGED_NIX_PATH.read_text()
    assert CONFIG_CHANGED_SENTINEL_BASENAME in kick_content
    assert "if [ -f" in kick_content
    assert "kickstart -k" in kick_content


def test_copy_script_drops_the_sentinel_only_on_a_real_config_change():
    copy_script_content = COPY_KARABINER_JSON_SCRIPT_PATH.read_text()
    assert CONFIG_CHANGED_SENTINEL_BASENAME in copy_script_content
    assert "cmp -s" in copy_script_content
    assert "touch" in copy_script_content
