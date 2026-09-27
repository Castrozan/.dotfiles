import json
import sys
import tomllib
from pathlib import Path


def verify(path, surface):
    configuration = (
        tomllib.loads(path.read_text())
        if surface == "codex"
        else json.loads(path.read_text())
    )
    hooks = configuration["hooks"]
    timeouts = {"SessionStart": 5, "PreToolUse": 5, "PostToolUse": 15, "Stop": 15}
    dispatchers = {
        "SessionStart": "session-start-dispatcher.py",
        "PreToolUse": "pre-tool-use-dispatcher.py",
        "PostToolUse": "post-tool-use-dispatcher.py",
        "Stop": "stop-dispatcher.py",
    }
    expected = set(timeouts)
    if surface == "claude":
        timeouts |= {"PreToolUse": 10, "Stop": 5, "SubagentStop": 5}
        dispatchers["SubagentStop"] = "stop-dispatcher.py"
        expected |= {"SubagentStop", "PermissionRequest"}
    else:
        assert configuration["features"]["hooks"] is True
    assert set(hooks) == expected, hooks
    for event, dispatcher in dispatchers.items():
        registrations = [hook for group in hooks[event] for hook in group["hooks"]]
        commands = [
            hook
            for hook in registrations
            if "herdr-agent-state.sh" not in hook["command"]
        ]
        assert len(commands) == 1, (event, commands)
        command = commands[0]
        assert command["type"] == "command"
        assert command["timeout"] == timeouts[event], (event, command)
        assert dispatcher in command["command"]
        assert "run-hook.sh" in command["command"]
        assert f"--surface={surface}" in command["command"]
        if event == "PreToolUse":
            assert "PROHIBITED_WORDS_ALLOWED=" in command["command"]
        if event == "SessionStart":
            assert any(group.get("matcher") == ".*" for group in hooks[event])
        if event == "PostToolUse" and surface == "claude":
            assert hooks[event][0]["matcher"] == "Skill|Edit|Write"
    if surface == "claude":
        exception = [
            hook for group in hooks["PermissionRequest"] for hook in group["hooks"]
        ]
        assert len(exception) == 1 and exception[0]["timeout"] == 1
        assert '"permissionDecision":"allow"' in exception[0]["command"]
        session = [hook for group in hooks["SessionStart"] for hook in group["hooks"]]
        herdr = [hook for hook in session if "herdr-agent-state.sh" in hook["command"]]
        assert len(herdr) == 1 and herdr[0]["timeout"] == 10
        assert herdr[0]["command"].endswith(" session")
    print(
        f"Verified {surface} native registrations, dispatchers, matchers and timeout budgets"
    )


if __name__ == "__main__":
    verify(Path(sys.argv[1]), sys.argv[2])
