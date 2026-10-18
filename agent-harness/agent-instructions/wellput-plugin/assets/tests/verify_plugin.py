import json
import re
import subprocess
import sys
import time
from pathlib import Path


def invoke(root, payload):
    result = subprocess.run(
        [sys.executable, "-S", str(root / "hooks/reply_hook.py")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=5,
        cwd="/",
        check=True,
    )
    return json.loads(result.stdout)


def verify(root):
    manifest = json.loads((root / "plugin.json").read_text())
    assert (
        manifest["$schema"]
        == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    )
    assert manifest["name"] == "wellput"
    assert not any(path.is_symlink() for path in root.rglob("*"))
    for path in (root / "skills").rglob("*.md"):
        text = path.read_text()
        assert "core-rules/" not in text
        assert "`url-shortener`" not in text
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            assert (path.parent / target.split("#")[0]).is_file(), (path, target)
    context = invoke(root, {"hook_event_name": "SessionStart"})
    policy = context["hookSpecificOutput"]["additionalContext"]
    assert "{{reply_format}}" not in policy
    assert "100 prose words" in policy
    assert str(root / "skills/wellput/SKILL.md") in policy
    assert (
        invoke(
            root,
            {"hook_event_name": "Stop", "last_assistant_message": "The check passed."},
        )
        == {}
    )
    rejected = invoke(
        root,
        {
            "hook_event_name": "Stop",
            "last_assistant_message": "Sure, PR #17 is ready — done.",
        },
    )
    assert rejected["decision"] == "block"
    assert "PR" in rejected["reason"] and "em dash" in rejected["reason"]
    assert (
        invoke(
            root,
            {
                "hook_event_name": "Stop",
                "last_assistant_message": "Sure, done.",
                "stop_hook_active": True,
            },
        )
        == {}
    )
    started = time.perf_counter()
    invoke(
        root,
        {"hook_event_name": "Stop", "reply_text": "“" * 16000 + " unquoted — result"},
    )
    assert time.perf_counter() - started < 2
    print(
        "Wellput package, dependency isolation, policy injection, reply repair, and bounded runtime verified."
    )


if __name__ == "__main__":
    verify(Path(sys.argv[1]).resolve())
