import json
import os
import subprocess
import sys

import pytest


def test_exported_skill_owns_session_replies_without_file_authoring(plugin_root):
    skill = plugin_root / "skills/wellput/SKILL.md"
    text = skill.read_text()
    assert "active agent sessions" in text
    assert "file authoring" in text
    assert "### Durable artifacts" not in text
    assert "artifact-writing.md" not in text
    assert not (skill.parent / "references/artifact-writing.md").exists()


def test_exported_instruction_prose_stays_wrapped_after_replacements(plugin_root):
    for path in (plugin_root / "skills").rglob("*.md"):
        text = path.read_text()
        if text.startswith("---\n"):
            text = text.partition("\n---\n")[2]
        assert all(len(line) <= 120 for line in text.splitlines()), path


@pytest.mark.parametrize(
    "reply",
    [
        "Absolutely",
        json.dumps({"summary": "evidence " * 120, "source": "PR #17"}),
        "| Name | Value |\n| --- | --- |\n| timeout | 30 |",
        "1. Stop the worker, then capture queue depth.\n2. Restore snapshot s-18.\n"
        "3. Start the worker.\n4. Wait for health status ready.\n5. Resume intake.",
    ],
)
def test_exported_stop_preserves_literal_and_structured_replies(plugin_root, reply):
    result = subprocess.run(
        [sys.executable, "-S", plugin_root / "hooks/reply_hook.py"],
        input=json.dumps({"hook_event_name": "Stop", "reply_text": reply}),
        capture_output=True,
        text=True,
        check=True,
        timeout=5,
        env=dict(os.environ, WELLPUT_CONFIG=str(plugin_root / "wellput.json")),
    )
    assert json.loads(result.stdout) == {}
