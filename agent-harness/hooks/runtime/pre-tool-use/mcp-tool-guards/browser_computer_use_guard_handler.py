from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

_MODULE_DIRECTORY = Path(__file__).resolve().parent
for _shared_module_candidate_directory in [_MODULE_DIRECTORY] + [
    ancestor / "common" for ancestor in _MODULE_DIRECTORY.parents
]:
    _shared_module_candidate_path = str(_shared_module_candidate_directory)
    if (
        _shared_module_candidate_directory.is_dir()
        and _shared_module_candidate_path not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_path)

from hook_dispatch import HandlerResult  # noqa: E402

COMPUTER_USE_TOOL_NAME_PREFIX = re.compile(r".*desktop[-_]computer[-_]use[-_]+")
CHROME_CONSENT_WINDOW_TITLE = "Allow remote debugging?"
CONSENT_CLICK_ACTION = "left_click"
CONSENT_CLICK_FOCUS_STRATEGY = "none"
WINDOW_DISCOVERY_ACTION = "list_windows"
APPLICATION_INPUT_KEYS = ("target_app", "bundle_id", "app")
WINDOW_INPUT_KEYS = ("target_window_id", "window_id")
WINDOW_LOOKUP_TIMEOUT_SECONDS = 2
BROWSER_APPLICATION_NAMES = frozenset(
    {
        "app.zen-browser.zen",
        "arc",
        "brave browser",
        "chromium",
        "com.apple.safari",
        "com.brave.browser",
        "com.google.chrome",
        "com.google.chrome.canary",
        "com.microsoft.edgemac",
        "company.thebrowser.browser",
        "firefox",
        "google chrome",
        "google chrome canary",
        "microsoft edge",
        "org.chromium.chromium",
        "org.mozilla.firefox",
        "safari",
        "zen",
    }
)
LIST_DESKTOP_WINDOWS_SCRIPT = (
    "ObjC.import('CoreGraphics');"
    "JSON.stringify(ObjC.deepUnwrap(ObjC.castRefToObject("
    "$.CGWindowListCopyWindowInfo(0, 0))).map(function (window) {"
    "return [window.kCGWindowNumber, window.kCGWindowOwnerName,"
    " window.kCGWindowName || ''];}))"
)
DENIAL_REASON = (
    "Computer use never drives a browser. Load the browser skill and use the "
    "chrome-devtools CLI: its click, fill and press_key commands dispatch real "
    "input events, and take_snapshot and take_screenshot observe the page. "
    "If chrome-devtools cannot do this, report that instead of working around it."
)


@dataclass(frozen=True)
class DesktopWindow:
    identifier: int
    owner_name: str
    title: str


def open_desktop_windows() -> list[DesktopWindow]:
    try:
        completed_lookup = subprocess.run(
            [
                "/usr/bin/osascript",
                "-l",
                "JavaScript",
                "-e",
                LIST_DESKTOP_WINDOWS_SCRIPT,
            ],
            capture_output=True,
            text=True,
            timeout=WINDOW_LOOKUP_TIMEOUT_SECONDS,
            check=False,
        )
        window_rows = json.loads(completed_lookup.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return []
    return [DesktopWindow(*window_row) for window_row in window_rows]


def is_browser_name(application_name) -> bool:
    return (
        isinstance(application_name, str)
        and application_name.strip().lower() in BROWSER_APPLICATION_NAMES
    )


def requested_window_identifier(tool_input):
    for window_input_key in WINDOW_INPUT_KEYS:
        window_identifier = tool_input.get(window_input_key)
        if isinstance(window_identifier, int):
            return window_identifier
    return None


def names_browser_application(tool_input) -> bool:
    return any(
        is_browser_name(tool_input.get(application_input_key))
        for application_input_key in APPLICATION_INPUT_KEYS
    )


def targets_browser(tool_input, window_identifier, desktop_windows) -> bool:
    for desktop_window in desktop_windows:
        if desktop_window.identifier == window_identifier:
            return is_browser_name(desktop_window.owner_name)
    return names_browser_application(tool_input)


def is_chrome_consent_click(action, tool_input, desktop_windows) -> bool:
    if action != CONSENT_CLICK_ACTION:
        return False
    if tool_input.get("focus_strategy") != CONSENT_CLICK_FOCUS_STRATEGY:
        return False
    return any(
        is_browser_name(desktop_window.owner_name)
        and desktop_window.title == CHROME_CONSENT_WINDOW_TITLE
        for desktop_window in desktop_windows
    )


def handle(hook_input):
    action = COMPUTER_USE_TOOL_NAME_PREFIX.sub("", hook_input.get("tool_name", ""))
    tool_input = hook_input.get("tool_input", {}) or {}
    if action == WINDOW_DISCOVERY_ACTION:
        return None
    window_identifier = requested_window_identifier(tool_input)
    if window_identifier is None and not names_browser_application(tool_input):
        return None
    desktop_windows = open_desktop_windows()
    if not targets_browser(tool_input, window_identifier, desktop_windows):
        return None
    if is_chrome_consent_click(action, tool_input, desktop_windows):
        return None
    return HandlerResult(decision="deny", reason=DENIAL_REASON)
