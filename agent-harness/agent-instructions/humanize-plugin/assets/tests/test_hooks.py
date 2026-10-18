import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def invoke(payload, root=ROOT):
    result = subprocess.run(
        [sys.executable, "-S", str(root / "hooks/humanize.py")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=5,
        cwd="/",
        check=True,
    )
    return json.loads(result.stdout)


@pytest.mark.parametrize("source", ["startup", "resume", "compact", "clear", "fork"])
def test_session_events_render_the_current_contract(source):
    output = invoke({"hook_event_name": "SessionStart", "source": source})
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "{{reply_format}}" not in context
    assert "100 prose words" in context
    assert str(ROOT / "skills/humanize/SKILL.md") in context


@pytest.mark.parametrize("field", ["reply_text", "last_assistant_message"])
def test_native_direct_reply_fields_trigger_a_repair(field):
    output = invoke({"hook_event_name": "Stop", field: "PR #17 is ready."})
    assert output["decision"] == "block"
    assert "gives no link" in output["reason"]


@pytest.mark.parametrize("codex", [False, True])
def test_transcript_fallback_reads_both_native_formats(tmp_path, codex):
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


def test_direct_reply_does_not_read_an_unavailable_transcript():
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


def test_a_retry_does_not_create_an_infinite_correction_loop():
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


def test_a_later_user_turn_does_not_validate_an_old_assistant_reply(tmp_path):
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


def test_relocation_with_spaces_preserves_policy_and_validation(tmp_path):
    destination = tmp_path / "humanize plugin"
    shutil.copytree(
        ROOT,
        destination,
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
    )
    policy = invoke({"hook_event_name": "SessionStart"}, destination)[
        "hookSpecificOutput"
    ]["additionalContext"]
    assert str(destination / "skills/humanize/SKILL.md") in policy
    assert (
        invoke(
            {"hook_event_name": "Stop", "reply_text": "PR #17 is ready."}, destination
        )["decision"]
        == "block"
    )


def test_invalid_configuration_fails_closed(tmp_path):
    destination = tmp_path / "invalid"
    shutil.copytree(
        ROOT,
        destination,
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
    )
    (destination / "hooks/rules/reply-formats.json").write_text("{}")
    output = invoke(
        {"hook_event_name": "Stop", "reply_text": "The check passed."}, destination
    )
    assert output["decision"] == "block"
    assert "could not run" in output["reason"]


def test_invalid_configuration_stops_policy_loading(tmp_path):
    destination = tmp_path / "invalid-session"
    shutil.copytree(
        ROOT,
        destination,
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
    )
    (destination / "hooks/rules/reply-formats.json").write_text("not json")
    output = invoke({"hook_event_name": "SessionStart"}, destination)
    assert output["continue"] is False
    assert "could not run" in output["stopReason"]


def test_custom_budgets_change_injected_policy_and_enforcement_together(tmp_path):
    destination = tmp_path / "custom"
    shutil.copytree(
        ROOT,
        destination,
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"),
    )
    path = destination / "hooks/rules/reply-formats.json"
    document = json.loads(path.read_text())
    document["formats"]["confirmation"] = {"maximum_words": 5, "grace_words": 0}
    path.write_text(json.dumps(document))
    policy = invoke({"hook_event_name": "SessionStart"}, destination)[
        "hookSpecificOutput"
    ]["additionalContext"]
    assert "5 prose words" in policy
    assert (
        invoke({"hook_event_name": "Stop", "reply_text": "word " * 6}, destination)[
            "decision"
        ]
        == "block"
    )
