import io
import json
import subprocess
import sys
from unittest.mock import Mock

import pytest

from hook_module_loader import (
    HOOK_SUBPROCESS_TIMEOUT_SECONDS,
    import_hyphenated_hook_module,
)
from flat_deploy_test_support import flatten_into_single_runtime_directory


@pytest.mark.parametrize("surface", ["codex", "claude", "opencode", "pi", "hermes"])
def test_prompt_title_handler_runs_only_on_codex(monkeypatch, surface):
    dispatcher = import_hyphenated_hook_module("user-prompt-submit-dispatcher")
    payload = {
        "hook_event_name": "UserPromptSubmit",
        "session_id": "first-prompt",
        "prompt": "Fix terminal title",
    }
    handler = Mock(return_value=None)
    monkeypatch.setattr(dispatcher.USER_PROMPT_SUBMIT_HANDLERS[0], "handle", handler)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    monkeypatch.setattr(sys, "argv", ["dispatcher", f"--surface={surface}"])
    with pytest.raises(SystemExit) as stopped:
        dispatcher.main()
    assert stopped.value.code == 0
    if surface == "codex":
        handler.assert_called_once()
        assert handler.call_args.args[0]["prompt"] == payload["prompt"]
    else:
        handler.assert_not_called()


def test_prompt_dispatcher_imports_after_flat_deployment(tmp_path):
    flatten_into_single_runtime_directory(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import runpy; "
            "dispatcher = runpy.run_path('user-prompt-submit-dispatcher.py'); "
            "handler = dispatcher['USER_PROMPT_SUBMIT_HANDLERS'][0].imported_handle(); "
            "assert handler.__module__ == 'codex_servant_status_handler'",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=HOOK_SUBPROCESS_TIMEOUT_SECONDS,
    )
    assert result.returncode == 0, result.stderr
