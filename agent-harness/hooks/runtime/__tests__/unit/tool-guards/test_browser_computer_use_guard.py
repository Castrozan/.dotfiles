import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from hook_dispatch import HookHandler, handler_matches_tool
from hook_module_loader import import_hyphenated_hook_module

guard = import_hyphenated_hook_module("browser_computer_use_guard_handler")
pre_tool_use_dispatcher = import_hyphenated_hook_module("pre-tool-use-dispatcher")

CLAUDE_PREFIX = "mcp__plugin_dotfiles_desktop-computer-use__"
CHROME_PAGE = guard.DesktopWindow(100, "Google Chrome", "Betha")
CHROME_CONSENT = guard.DesktopWindow(101, "Google Chrome", "Allow remote debugging?")
TERMINAL = guard.DesktopWindow(200, "Ghostty", "shell")


@pytest.fixture
def desktop_windows(monkeypatch):
    def install(*windows):
        monkeypatch.setattr(guard, "open_desktop_windows", lambda: list(windows))

    install(CHROME_PAGE, TERMINAL)
    return install


def decide(action, tool_input):
    return guard.handle(
        {"tool_name": f"{CLAUDE_PREFIX}{action}", "tool_input": tool_input}
    )


def computer_use_handler():
    return next(
        handler
        for handler in pre_tool_use_dispatcher.PRE_TOOL_USE_HANDLERS
        if handler.handler_module_name == "browser_computer_use_guard_handler"
    )


@pytest.mark.parametrize(
    "action,tool_input",
    [
        ("left_click", {"coordinate": [1, 1], "target_app": "com.google.Chrome"}),
        ("key", {"text": "cmd+l", "target_app": "Google Chrome"}),
        ("screenshot", {"target_app": "com.apple.Safari"}),
        ("activate_app", {"bundle_id": "com.google.Chrome"}),
        ("activate_app", {"app": "com.brave.Browser"}),
        ("open_application", {"bundle_id": "org.mozilla.firefox"}),
        ("left_click", {"coordinate": [1, 1], "target_window_id": 100}),
        ("activate_window", {"window_id": 100}),
        ("find_element", {"label": "Catálogo", "target_window_id": 100}),
    ],
)
def test_denies_computer_use_that_targets_a_browser(
    desktop_windows, action, tool_input
):
    assert decide(action, tool_input).decision == "deny"


@pytest.mark.parametrize(
    "action,tool_input",
    [
        ("left_click", {"coordinate": [1, 1], "target_window_id": 200}),
        (
            "left_click",
            {"coordinate": [1, 1], "target_app": "com.fortinet.FortiClient"},
        ),
        ("open_application", {"bundle_id": "com.fortinet.FortiClient"}),
        ("screenshot", {}),
        ("list_windows", {"bundle_id": "com.google.Chrome"}),
        ("left_click", {"coordinate": [1, 1], "target_window_id": 999}),
    ],
)
def test_allows_computer_use_that_does_not_target_a_browser(
    desktop_windows, action, tool_input
):
    assert decide(action, tool_input) is None


def test_window_identifier_takes_precedence_over_a_named_browser(desktop_windows):
    tool_input = {
        "coordinate": [1, 1],
        "target_app": "com.google.Chrome",
        "target_window_id": 200,
    }
    assert decide("left_click", tool_input) is None


@pytest.mark.parametrize(
    "target", [{"target_app": "com.google.Chrome"}, {"target_window_id": 101}]
)
def test_allows_the_consent_click_while_the_prompt_is_open(desktop_windows, target):
    desktop_windows(CHROME_PAGE, CHROME_CONSENT)
    assert (
        decide("left_click", {"coordinate": [1, 1], "focus_strategy": "none", **target})
        is None
    )


@pytest.mark.parametrize(
    "action,focus_strategy",
    [("left_click", "strict"), ("left_click", None), ("double_click", "none")],
)
def test_consent_exemption_requires_the_exact_click_shape(
    desktop_windows, action, focus_strategy
):
    desktop_windows(CHROME_PAGE, CHROME_CONSENT)
    tool_input = {"coordinate": [1, 1], "target_app": "com.google.Chrome"}
    if focus_strategy:
        tool_input["focus_strategy"] = focus_strategy
    assert decide(action, tool_input).decision == "deny"


def test_denies_a_consent_shaped_click_when_no_prompt_is_open(desktop_windows):
    tool_input = {
        "coordinate": [1, 1],
        "focus_strategy": "none",
        "target_app": "com.google.Chrome",
    }
    assert decide("left_click", tool_input).decision == "deny"


def test_named_browser_is_still_denied_when_window_lookup_fails(monkeypatch):
    monkeypatch.setattr(guard, "open_desktop_windows", lambda: [])
    assert decide("key", {"target_app": "com.google.Chrome"}).decision == "deny"


@pytest.mark.parametrize(
    "tool_name",
    [
        "mcp__plugin_dotfiles_desktop-computer-use__left_click",
        "mcp__desktop-computer-use__left_click",
        "desktop-computer-use_left_click",
    ],
)
def test_dispatcher_routes_every_harness_tool_name_to_the_guard(tool_name):
    assert handler_matches_tool(computer_use_handler(), tool_name)


@pytest.mark.parametrize("tool_name", ["Bash", "mcp__codex__codex", "Read"])
def test_dispatcher_keeps_other_tools_away_from_the_guard(tool_name):
    assert isinstance(computer_use_handler(), HookHandler)
    assert not handler_matches_tool(computer_use_handler(), tool_name)
