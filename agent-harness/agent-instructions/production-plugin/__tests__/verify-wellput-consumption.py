import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def invoke(scripts, payload, environment):
    completed = subprocess.run(
        [
            str(scripts / "run-hook.sh"),
            str(
                scripts
                / (
                    "session-start-dispatcher.py"
                    if payload["hook_event_name"] == "SessionStart"
                    else "stop-dispatcher.py"
                )
            ),
            "--surface=pi",
        ],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
        env=environment,
    )
    return json.loads(completed.stdout or "{}")


def verify(bundle):
    package = bundle / "plugin"
    upstream = package / "native/wellput"
    scripts = package / "hooks"
    assert json.loads((upstream / "plugin.json").read_text())["name"] == "wellput"
    assert (package / "skills/wellput/SKILL.md").read_bytes() == (
        upstream / "skills/wellput/SKILL.md"
    ).read_bytes()
    assert not (package / "skills/humanize").exists()
    assert not (package / "library/skills/humanize").exists()
    assert not (scripts / "reply_rule_catalog.py").exists()
    assert not (scripts / "end_of_turn_format_guard_handler.py").exists()
    environment = {
        name: value
        for name, value in os.environ.items()
        if name not in ("CLAWDE_AGENT_NAME", "WELLPUT_CONFIG")
    }
    environment["AGENT_INTERACTIVE_PREFERENCES_PATH"] = "/session-policy.md"
    valid_reply = {
        "hook_event_name": "Stop",
        "reply_text": "The uploaded artifact is ready for inspection.",
    }
    accepted = invoke(scripts, valid_reply, environment)
    assert accepted == {}, accepted
    rejected = invoke(
        scripts, {"hook_event_name": "Stop", "reply_text": "Ready — done."}, environment
    )
    assert rejected["decision"] == "block"
    background = environment | {"CLAWDE_AGENT_NAME": ""}
    assert (
        invoke(
            scripts,
            {"hook_event_name": "Stop", "reply_text": "Ready — done."},
            background,
        )
        == {}
    )
    with tempfile.TemporaryDirectory() as directory:
        config = json.loads((upstream / "wellput.json").read_text())
        config["formats"]["confirmation"] = {"maximum_words": 2, "grace_words": 0}
        configuration = Path(directory) / "config.json"
        configuration.write_text(json.dumps(config))
        configured = environment | {"WELLPUT_CONFIG": str(configuration)}
        startup = invoke(scripts, {"hook_event_name": "SessionStart"}, configured)
        context = startup["hookSpecificOutput"]["additionalContext"]
        assert "2 prose words" in context
        assert "skills/wellput/SKILL.md" in context
        assert "Humanize" not in context
        assert invoke(scripts, valid_reply, configured)["decision"] == "block"
        configuration.write_text("{}")
        assert (
            invoke(scripts, {"hook_event_name": "SessionStart"}, configured)["continue"]
            is False
        )
    print(
        "Pinned Wellput skill, single validator, configured startup, repair, and background exclusion verified."
    )


if __name__ == "__main__":
    verify(Path(sys.argv[1]))
