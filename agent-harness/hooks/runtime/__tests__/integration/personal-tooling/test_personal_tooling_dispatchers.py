import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from flat_deploy_test_support import flatten_into_single_runtime_directory

HOOK_ROOT = Path(__file__).resolve().parents[3]

DISPATCHERS = (
    ("SessionStart", "session-start/session-start-dispatcher.py"),
    ("UserPromptSubmit", "user-prompt-submit/user-prompt-submit-dispatcher.py"),
    ("PreToolUse", "pre-tool-use/pre-tool-use-dispatcher.py"),
)


@pytest.mark.parametrize("event_name,relative_script", DISPATCHERS)
@pytest.mark.parametrize("surface", ("claude", "codex", "opencode", "pi", "hermes"))
@pytest.mark.parametrize("flattened", (False, True))
def test_only_claude_is_blocked_in_source_and_flat_deploy(
    tmp_path, event_name, relative_script, surface, flattened
):
    script = HOOK_ROOT / relative_script
    if flattened:
        runtime = tmp_path / "runtime"
        runtime.mkdir()
        flatten_into_single_runtime_directory(runtime)
        script = runtime / script.name
    payload = {
        "hook_event_name": event_name,
        "cwd": str(tmp_path / ".dotfiles"),
        "session_id": "personal-tooling-test",
        "tool_name": "Read" if event_name == "PreToolUse" else "",
        "tool_input": {"file_path": "/etc/hosts"},
    }
    environment = dict(os.environ, HOME=str(tmp_path), CLAWDE_AGENT_NAME="policy-probe")
    environment.pop("AGENT_EVALS_SOURCE_ROOT", None)
    environment.pop("AGENT_INTERACTIVE_PREFERENCES_PATH", None)
    completed = subprocess.run(
        [sys.executable, str(script), f"--surface={surface}"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=environment,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    output = json.loads(completed.stdout) if completed.stdout.strip() else {}
    if surface != "claude":
        assert output.get("continue") is not False
        assert output.get("hookSpecificOutput", {}).get("permissionDecision") != "deny"
    elif event_name == "PreToolUse":
        assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "Use Codex" in output["hookSpecificOutput"]["permissionDecisionReason"]
    else:
        assert output["continue"] is False
        assert "Use Codex" in output["stopReason"]
