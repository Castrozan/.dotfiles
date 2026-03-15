import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
WINDOWS_SCRIPTS_DIR = SCRIPTS_DIR / "windows"
WINDOWS_LIB_DIR = WINDOWS_SCRIPTS_DIR / "lib"
HARDWARE_SCRIPTS_DIR = SCRIPTS_DIR / "hardware"
LAUNCHERS_SCRIPTS_DIR = SCRIPTS_DIR / "launchers"
THEME_SCRIPTS_DIR = SCRIPTS_DIR / "theme"
UTILITIES_SCRIPTS_DIR = SCRIPTS_DIR / "utilities"

sys.path.insert(0, str(WINDOWS_LIB_DIR))
sys.path.insert(0, str(WINDOWS_SCRIPTS_DIR))
sys.path.insert(0, str(HARDWARE_SCRIPTS_DIR))
sys.path.insert(0, str(LAUNCHERS_SCRIPTS_DIR))
sys.path.insert(0, str(THEME_SCRIPTS_DIR))
sys.path.insert(0, str(UTILITIES_SCRIPTS_DIR))


@pytest.fixture
def mock_subprocess_run():
    with patch("hyprland_ipc.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        yield mock_run


@pytest.fixture
def hyprctl_response_builder(mock_subprocess_run):
    canned_responses = {}

    def set_response(subcommand: str, response_data):
        import json

        if response_data is None:
            canned_responses[("hyprctl", subcommand, "-j")] = ""
            canned_responses[("hyprctl", subcommand)] = ""
        elif isinstance(response_data, (dict, list)):
            json_output = json.dumps(response_data)
            canned_responses[("hyprctl", subcommand, "-j")] = json_output
            canned_responses[("hyprctl", subcommand, "all", "-j")] = json_output
            canned_responses[("hyprctl", subcommand)] = json_output
        else:
            canned_responses[("hyprctl", subcommand)] = str(response_data)

    def side_effect(args, **kwargs):
        key = tuple(args)
        result = MagicMock()
        result.returncode = 0
        result.stdout = canned_responses.get(key, "")
        if not result.stdout:
            for stored_key, stored_value in canned_responses.items():
                if all(part in args for part in stored_key):
                    result.stdout = stored_value
                    break
        return result

    mock_subprocess_run.side_effect = side_effect

    return set_response


@pytest.fixture
def sample_hyprland_clients():
    return [
        {
            "address": "0xaaa",
            "workspace": {"id": 1},
            "class": "kitty",
            "title": "Terminal",
            "pid": 1234,
            "floating": False,
            "pinned": False,
            "fullscreen": 0,
            "grouped": ["0xaaa", "0xbbb"],
            "focusHistoryID": 0,
        },
        {
            "address": "0xbbb",
            "workspace": {"id": 1},
            "class": "firefox",
            "title": "Browser",
            "pid": 5678,
            "floating": False,
            "pinned": False,
            "fullscreen": 0,
            "grouped": ["0xaaa", "0xbbb"],
            "focusHistoryID": 1,
        },
        {
            "address": "0xccc",
            "workspace": {"id": 2},
            "class": "code",
            "title": "Editor",
            "pid": 9012,
            "floating": False,
            "pinned": False,
            "fullscreen": 1,
            "grouped": [],
            "focusHistoryID": 2,
        },
        {
            "address": "0xddd",
            "workspace": {"id": 1},
            "class": "pavucontrol",
            "title": "Volume",
            "pid": 3456,
            "floating": True,
            "pinned": False,
            "fullscreen": 0,
            "grouped": [],
            "focusHistoryID": 3,
        },
        {
            "address": "0xeee",
            "workspace": {"id": 1},
            "class": "com.gabm.satty",
            "title": "Satty",
            "pid": 7890,
            "floating": True,
            "pinned": True,
            "fullscreen": 0,
            "grouped": [],
            "focusHistoryID": 4,
        },
    ]


@pytest.fixture
def sample_hyprland_workspaces():
    return [
        {"id": 1, "hasfullscreen": True},
        {"id": 2, "hasfullscreen": True},
        {"id": 3, "hasfullscreen": False},
    ]


@pytest.fixture
def temporary_history_file(tmp_path):
    history_file = tmp_path / "hypr-closed-windows-history"
    return history_file
