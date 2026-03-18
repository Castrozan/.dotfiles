import importlib.machinery
import importlib.util
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

mock_appkit = MagicMock()
mock_appkit.NSPanel = type("NSPanel", (), {})

mock_apphelper = MagicMock()
mock_apphelper.callAfter = lambda func, *args: func(*args)

mock_pyobjctools = MagicMock()
mock_pyobjctools.AppHelper = mock_apphelper

sys.modules["AppKit"] = mock_appkit
sys.modules["objc"] = MagicMock()
sys.modules["Foundation"] = MagicMock()
sys.modules["PyObjCTools"] = mock_pyobjctools
sys.modules["PyObjCTools.AppHelper"] = mock_apphelper

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
DAEMON_SCRIPT_PATH = str(SCRIPTS_DIR / "workspace-window-switcher-daemon")

loader = importlib.machinery.SourceFileLoader(
    "workspace_window_switcher_daemon", DAEMON_SCRIPT_PATH
)
spec = importlib.util.spec_from_loader("workspace_window_switcher_daemon", loader)
daemon_module = importlib.util.module_from_spec(spec)
sys.modules["workspace_window_switcher_daemon"] = daemon_module
spec.loader.exec_module(daemon_module)


class ImmediateThread:
    def __init__(self, target=None, daemon=False, **kwargs):
        self._target = target

    def start(self):
        if self._target:
            self._target()


@pytest.fixture(autouse=True)
def synchronous_threads():
    with patch.object(daemon_module.threading, "Thread", ImmediateThread):
        yield


@pytest.fixture(autouse=True)
def mock_commit_timers():
    with patch.object(daemon_module.threading, "Timer") as mock_timer:
        mock_timer_instance = MagicMock()
        mock_timer.return_value = mock_timer_instance
        yield mock_timer


@pytest.fixture(autouse=True)
def temporary_active_flag_path(tmp_path):
    flag_path = str(tmp_path / "workspace-switcher.active")
    with patch.object(daemon_module, "ACTIVE_FLAG_PATH", flag_path):
        yield flag_path


@pytest.fixture
def mock_aerospace_provider():
    provider = MagicMock()
    provider.get_focused_workspace_windows.return_value = []
    provider.get_focused_window_id.return_value = None
    provider.focus_window.return_value = None
    return provider


@pytest.fixture
def mock_overlay():
    return MagicMock()


@pytest.fixture
def sample_workspace_windows():
    return [
        {"window-id": 1001, "app-name": "WezTerm", "window-title": "~/dotfiles"},
        {"window-id": 1002, "app-name": "Brave Browser", "window-title": "GitHub"},
        {"window-id": 1003, "app-name": "Slack", "window-title": "#engineering"},
        {"window-id": 1004, "app-name": "Finder", "window-title": "Downloads"},
    ]


@pytest.fixture
def switcher_state(mock_aerospace_provider, mock_overlay):
    return daemon_module.WindowSwitcherStateMachine(
        mock_aerospace_provider, mock_overlay
    )


@pytest.fixture
def aerospace_provider_with_windows(mock_aerospace_provider, sample_workspace_windows):
    mock_aerospace_provider.get_focused_workspace_windows.return_value = (
        sample_workspace_windows
    )
    mock_aerospace_provider.get_focused_window_id.return_value = 1001
    return mock_aerospace_provider
