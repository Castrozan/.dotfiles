import json
import os
import shutil
import stat
import subprocess
import sys

import pytest


@pytest.fixture
def invoke(plugin_root, tmp_path):
    def invoke_hook(payload, root=plugin_root, environment=None):
        hook_environment = dict(os.environ, XDG_CONFIG_HOME=str(tmp_path / "config"))
        hook_environment.pop("WELLPUT_CONFIG", None)
        hook_environment.update(environment or {})
        result = subprocess.run(
            [sys.executable, "-S", str(root / "hooks/reply_hook.py")],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=5,
            cwd="/",
            env=hook_environment,
            check=True,
        )
        return json.loads(result.stdout)

    return invoke_hook


def copy_plugin(plugin_root, destination):
    shutil.copytree(
        plugin_root,
        destination,
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
    )
    for path in (destination, *destination.rglob("*")):
        path.chmod(path.stat().st_mode | stat.S_IWUSR)


@pytest.mark.parametrize("source", ["startup", "resume", "compact", "clear", "fork"])
def test_session_events_render_the_current_contract(source, invoke, plugin_root):
    output = invoke({"hook_event_name": "SessionStart", "source": source})
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "{{reply_format}}" not in context
    assert "100 prose words" in context
    assert str(plugin_root / "skills/wellput/SKILL.md") in context


@pytest.mark.parametrize("field", ["reply_text", "last_assistant_message"])
def test_native_direct_reply_fields_trigger_a_repair(field, invoke):
    output = invoke({"hook_event_name": "Stop", field: "PR #17 is ready."})
    assert output["decision"] == "block"
    assert "gives no link" in output["reason"]


@pytest.mark.parametrize("codex", [False, True])
def test_transcript_fallback_reads_both_native_formats(tmp_path, codex, invoke):
    content = [{"type": "output_text" if codex else "text", "text": "Sure, done."}]
    message = {"type": "message", "role": "assistant", "content": content}
    event = (
        {"type": "response_item", "payload": message}
        if codex
        else {"type": "assistant", "message": message}
    )
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text("incomplete json\n" + json.dumps(event))
    output = invoke({"hook_event_name": "Stop", "transcript_path": str(transcript)})
    assert output["decision"] == "block"
    assert "reaction" in output["reason"]


def test_direct_reply_does_not_read_an_unavailable_transcript(invoke):
    assert (
        invoke(
            {
                "hook_event_name": "Stop",
                "last_assistant_message": "The check passed.",
                "transcript_path": "/unavailable/transcript",
            }
        )
        == {}
    )


def test_a_retry_does_not_create_an_infinite_correction_loop(invoke):
    assert (
        invoke(
            {
                "hook_event_name": "Stop",
                "reply_text": "Sure, done.",
                "stop_hook_active": True,
            }
        )
        == {}
    )


def test_a_later_user_turn_does_not_validate_an_old_assistant_reply(tmp_path, invoke):
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text(
        "\n".join(
            json.dumps(event)
            for event in [
                {"type": "assistant", "message": {"content": "Sure, done."}},
                {"type": "user", "message": {"content": "Continue."}},
            ]
        )
    )
    assert invoke({"hook_event_name": "Stop", "transcript_path": str(transcript)}) == {}


def test_relocation_with_spaces_preserves_policy_and_validation(
    tmp_path, invoke, plugin_root
):
    destination = tmp_path / "wellput plugin"
    copy_plugin(plugin_root, destination)
    policy = invoke({"hook_event_name": "SessionStart"}, destination)[
        "hookSpecificOutput"
    ]["additionalContext"]
    assert str(destination / "skills/wellput/SKILL.md") in policy
    assert (
        invoke(
            {"hook_event_name": "Stop", "reply_text": "PR #17 is ready."}, destination
        )["decision"]
        == "block"
    )


@pytest.mark.parametrize("document", ["not json", "{}"])
def test_invalid_configuration_fails_closed(tmp_path, invoke, plugin_root, document):
    destination = tmp_path / "invalid"
    copy_plugin(plugin_root, destination)
    (destination / "wellput.json").write_text(document)
    output = invoke(
        {"hook_event_name": "Stop", "reply_text": "The check passed."}, destination
    )
    assert output["decision"] == "block"
    assert "could not run" in output["reason"]

    output = invoke({"hook_event_name": "SessionStart"}, destination)
    assert output["continue"] is False
    assert "could not run" in output["stopReason"]


@pytest.mark.parametrize("selection", ["bundled", "xdg", "explicit"])
def test_selected_configuration_changes_policy_and_enforcement_together(
    tmp_path, invoke, plugin_root, selection
):
    destination = tmp_path / "custom"
    copy_plugin(plugin_root, destination)
    document = json.loads((destination / "wellput.json").read_text())
    document["formats"]["confirmation"] = {"maximum_words": 5, "grace_words": 0}
    path = {
        "bundled": destination / "wellput.json",
        "xdg": tmp_path / "config/wellput/config.json",
        "explicit": tmp_path / "explicit.json",
    }[selection]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document))
    environment = {"WELLPUT_CONFIG": str(path)} if selection == "explicit" else {}
    if selection == "explicit":
        user_path = tmp_path / "config/wellput/config.json"
        user_path.parent.mkdir(parents=True, exist_ok=True)
        user_path.write_text("invalid user config overridden by explicit path")
    policy = invoke({"hook_event_name": "SessionStart"}, destination, environment)[
        "hookSpecificOutput"
    ]["additionalContext"]
    assert "5 prose words" in policy
    assert (
        invoke(
            {"hook_event_name": "Stop", "reply_text": "word " * 6},
            destination,
            environment,
        )["decision"]
        == "block"
    )


@pytest.mark.parametrize("content", [None, "not json", "{}"])
def test_explicit_invalid_config_never_falls_back(tmp_path, invoke, content):
    path = tmp_path / "explicit.json"
    if content is not None:
        path.write_text(content)
    environment = {"WELLPUT_CONFIG": str(path)}
    assert (
        invoke({"hook_event_name": "SessionStart"}, environment=environment)["continue"]
        is False
    )
    assert (
        invoke(
            {"hook_event_name": "Stop", "reply_text": "Done."}, environment=environment
        )["decision"]
        == "block"
    )
