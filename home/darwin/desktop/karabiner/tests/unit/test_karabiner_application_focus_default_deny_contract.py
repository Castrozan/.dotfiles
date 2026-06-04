from pathlib import Path

KARABINER_DIRECTORY = Path(__file__).parent.parent.parent
APPLICATION_FOCUS_GUARDS_NIX_PATH = (
    KARABINER_DIRECTORY / "rules" / "application-focus-default-deny-guards.nix"
)
RULES_DEFAULT_NIX_PATH = KARABINER_DIRECTORY / "rules" / "default.nix"
BRAVE_KEYBIND_PASSTHROUGH_NIX_PATH = (
    KARABINER_DIRECTORY / "rules" / "brave-keybind-passthrough-rules.nix"
)
HAMMERSPOON_APPLICATION_FOCUS_MODULE_PATH = (
    KARABINER_DIRECTORY.parent
    / "hammerspoon"
    / "karabiner_application_focus_variables.lua"
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

APPLICATION_FOCUS_VARIABLE_NAMES = (
    "terminal_application_is_frontmost",
    "non_terminal_application_is_frontmost",
    "brave_browser_is_frontmost",
)
CONFIG_CHANGED_SENTINEL_BASENAME = "karabiner-config-changed-since-last-kick"


def test_guard_file_is_the_single_source_of_truth_for_all_variable_names():
    guard_content = APPLICATION_FOCUS_GUARDS_NIX_PATH.read_text()
    assert "makeApplicationFocusDefaultDenyCondition" in guard_content
    assert '"variable_if"' in guard_content
    assert "value = 1;" in guard_content
    for application_focus_variable_name in APPLICATION_FOCUS_VARIABLE_NAMES:
        assert application_focus_variable_name in guard_content


def test_rules_default_guards_both_terminal_directions_from_the_guard():
    rules_default_content = RULES_DEFAULT_NIX_PATH.read_text()
    assert "application-focus-default-deny-guards.nix" in rules_default_content
    assert "nonTerminalApplicationIsFrontmost" in rules_default_content
    assert "terminalApplicationIsFrontmost" in rules_default_content


def test_brave_rules_guard_their_frontmost_passthrough_from_the_guard():
    brave_content = BRAVE_KEYBIND_PASSTHROUGH_NIX_PATH.read_text()
    assert "application-focus-default-deny-guards.nix" in brave_content
    assert "braveBrowserIsFrontmost" in brave_content


def test_hammerspoon_sets_every_application_focus_variable_the_guards_read():
    hammerspoon_content = HAMMERSPOON_APPLICATION_FOCUS_MODULE_PATH.read_text()
    for application_focus_variable_name in APPLICATION_FOCUS_VARIABLE_NAMES:
        assert application_focus_variable_name in hammerspoon_content


def test_hammerspoon_reports_terminal_and_brave_focus_consistently():
    hammerspoon_content = HAMMERSPOON_APPLICATION_FOCUS_MODULE_PATH.read_text()
    assert "frontmostIsTerminal and 1 or 0" in hammerspoon_content
    assert "frontmostIsTerminal and 0 or 1" in hammerspoon_content
    assert "frontmostIsBraveBrowser and 1 or 0" in hammerspoon_content


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
