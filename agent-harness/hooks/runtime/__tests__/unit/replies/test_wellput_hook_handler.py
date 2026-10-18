import json
import subprocess
from types import SimpleNamespace

import pytest

import wellput_hook_handler


@pytest.fixture
def public_hook(monkeypatch):
    monkeypatch.setenv("AGENT_INTERACTIVE_PREFERENCES_PATH", "/session-policy.md")
    monkeypatch.delenv("CLAWDE_AGENT_NAME", raising=False)
    monkeypatch.setenv("DOTFILES_WELLPUT_HOOK", "/wellput/hooks/reply_hook.py")
    calls = []

    def respond(document):
        def run(command, **arguments):
            calls.append((command, arguments))
            return SimpleNamespace(stdout=json.dumps(document))

        monkeypatch.setattr(wellput_hook_handler.subprocess, "run", run)

    return calls, respond


def test_stop_delegates_the_original_payload_to_the_public_hook(public_hook):
    calls, respond = public_hook
    respond({"decision": "block", "reason": "repair from Wellput"})
    payload = {"hook_event_name": "Stop", "transcript_path": "/session.jsonl"}
    result = wellput_hook_handler.handle(payload)
    command, arguments = calls[0]
    assert command[1:] == ["-S", "/wellput/hooks/reply_hook.py"]
    assert json.loads(arguments["input"]) == payload
    assert arguments["timeout"] == 5
    assert result.decision == "block"
    assert result.reason == "repair from Wellput"


def test_session_start_uses_the_public_configuration_context(public_hook):
    _, respond = public_hook
    respond({"hookSpecificOutput": {"additionalContext": "configured Wellput rules"}})
    result = wellput_hook_handler.handle({"hook_event_name": "SessionStart"})
    assert result.additional_context == "configured Wellput rules"


@pytest.mark.parametrize("interactive,background", [(False, False), (True, True)])
def test_nonhuman_sessions_do_not_invoke_wellput(
    public_hook, monkeypatch, interactive, background
):
    calls, _ = public_hook
    if not interactive:
        monkeypatch.delenv("AGENT_INTERACTIVE_PREFERENCES_PATH")
    if background:
        monkeypatch.setenv("CLAWDE_AGENT_NAME", "")
    assert wellput_hook_handler.handle({"hook_event_name": "Stop"}) is None
    assert calls == []


def test_unavailable_wellput_blocks_instead_of_using_local_rules(
    public_hook, monkeypatch
):
    def unavailable(*arguments, **keywords):
        raise subprocess.TimeoutExpired("wellput", 5)

    monkeypatch.setattr(wellput_hook_handler.subprocess, "run", unavailable)
    result = wellput_hook_handler.handle({"hook_event_name": "Stop"})
    assert result.decision == "block"
    assert "Wellput" in result.reason


def test_invalid_startup_configuration_blocks_the_session(public_hook):
    _, respond = public_hook
    respond({"continue": False, "stopReason": "invalid Wellput configuration"})
    result = wellput_hook_handler.handle({"hook_event_name": "SessionStart"})
    assert result.decision == "block"
    assert result.reason == "invalid Wellput configuration"


def test_startup_denial_is_not_silently_dropped(capsys):
    from hook_event_output import emit_context_injection

    outcome = SimpleNamespace(decision="block", reason="Wellput configuration failed")
    emit_context_injection("SessionStart", outcome)
    assert json.loads(capsys.readouterr().out) == {
        "continue": False,
        "stopReason": "Wellput configuration failed",
    }


def test_malformed_wellput_context_blocks_instead_of_breaking_injection(public_hook):
    _, respond = public_hook
    respond({"hookSpecificOutput": {"additionalContext": ["invalid"]}})
    result = wellput_hook_handler.handle({"hook_event_name": "SessionStart"})
    assert result.decision == "block"
    assert "must be text" in result.reason
