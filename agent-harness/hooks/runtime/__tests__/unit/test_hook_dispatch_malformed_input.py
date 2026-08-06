import json
import subprocess
import sys
from pathlib import Path

import pytest

from hook_module_loader import HOOK_SUBPROCESS_TIMEOUT_SECONDS

HOOKS_ROOT = Path(__file__).resolve().parents[2]

DISPATCHER_PATHS = [
    next(HOOKS_ROOT.rglob(dispatcher_name))
    for dispatcher_name in (
        "pre-tool-use-dispatcher.py",
        "post-tool-use-dispatcher.py",
        "stop-dispatcher.py",
        "session-start-dispatcher.py",
    )
]

VALID_JSON_THAT_IS_NOT_AN_OBJECT = [
    "null",
    "[1,2,3]",
    '"just a string"',
    "42",
    "true",
]


@pytest.mark.parametrize("dispatcher_path", DISPATCHER_PATHS, ids=lambda p: p.name)
@pytest.mark.parametrize("raw_input", VALID_JSON_THAT_IS_NOT_AN_OBJECT)
def test_dispatchers_exit_cleanly_on_valid_json_that_is_not_an_object(
    dispatcher_path, raw_input
):
    result = subprocess.run(
        [sys.executable, str(dispatcher_path)],
        input=raw_input,
        capture_output=True,
        text=True,
        timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS,
    )
    assert result.returncode == 0, result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("dispatcher_path", DISPATCHER_PATHS, ids=lambda p: p.name)
def test_dispatchers_exit_cleanly_on_undecodable_input(dispatcher_path):
    result = subprocess.run(
        [sys.executable, str(dispatcher_path)],
        input="{not json at all",
        capture_output=True,
        text=True,
        timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS,
    )
    assert result.returncode == 0, result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("dispatcher_path", DISPATCHER_PATHS, ids=lambda p: p.name)
def test_dispatchers_exit_cleanly_on_wrongly_typed_tool_input(dispatcher_path):
    payload = json.dumps(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": "not a dictionary",
        }
    )
    result = subprocess.run(
        [sys.executable, str(dispatcher_path)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS,
    )
    assert result.returncode == 0, result.stderr
    assert "Traceback" not in result.stderr
