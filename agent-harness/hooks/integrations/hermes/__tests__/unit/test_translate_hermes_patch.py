import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

import translate_hermes_hook_call as translator


@pytest.mark.parametrize("private_target", [False, True])
@pytest.mark.parametrize("precheck_path", [None, "private-configuration/precheck.md"])
def test_native_v4a_patch_contents_reach_public_content_guard(
    tmp_path, private_target, precheck_path
):
    hooks_root = Path(__file__).resolve().parents[4]
    guard_path = (
        hooks_root
        / "runtime/pre-tool-use/prohibited-words-guard/prohibited_words_guard_handler.py"
    )
    dispatcher = tmp_path / "dispatcher"
    capture_path = tmp_path / "capture.json"
    prohibited_words_path = tmp_path / "words.txt"
    prohibited_words_path.write_text("transportblockedword\n")
    dispatcher.write_text(
        f"#!{sys.executable}\n"
        "import json\n"
        "from pathlib import Path\n"
        "import runpy\n"
        "import sys\n"
        "payload = json.load(sys.stdin)\n"
        f"Path({str(capture_path)!r}).write_text(json.dumps(payload))\n"
        f"result = runpy.run_path({str(guard_path)!r})['handle'](payload)\n"
        "if result is not None:\n"
        "    print(json.dumps({'hookSpecificOutput': {\n"
        "        'permissionDecision': result.decision,\n"
        "        'permissionDecisionReason': result.reason,\n"
        "    }}))\n"
    )
    dispatcher.chmod(0o755)
    target_path = (
        tmp_path / "private-configuration" / "secret.md"
        if private_target
        else tmp_path / "public.md"
    )
    patch_text = (
        f"*** Begin Patch\n*** Add File: {target_path}\n"
        "+transportblockedword\n*** End Patch\n"
    )
    native_input = {"mode": "patch", "patch": patch_text, "opaque": [1, 2]}
    if precheck_path is not None:
        native_input["path"] = str(tmp_path / precheck_path)
    completed = subprocess.run(
        [sys.executable, translator.__file__, str(dispatcher)],
        input=json.dumps(
            {
                "hook_event_name": "pre_tool_call",
                "tool_name": "patch",
                "tool_input": native_input,
                "cwd": str(tmp_path),
            }
        ),
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PROHIBITED_WORDS_FILE": str(prohibited_words_path),
            "PROHIBITED_WORDS_ALLOWED": "",
        },
        timeout=5.0,
    )
    assert completed.returncode == 0
    assert completed.stderr == ""
    if not private_target:
        assert completed.stdout, "native V4A public content bypassed the guard"
    payload = json.loads(capture_path.read_text())
    assert payload["tool_name"] == "apply_patch"
    assert payload["tool_input"] == {
        "mode": "patch",
        "patch_text": patch_text,
        "opaque": [1, 2],
    }
    if private_target:
        assert completed.stdout == ""
    else:
        response = json.loads(completed.stdout)
        assert response["decision"] == "block"
        assert "transportblockedword" in response["reason"]
