import subprocess
from types import SimpleNamespace

import pytest

import herdr_pace_reply_capture_handler as capture
from hook_module_loader import import_hyphenated_hook_module


@pytest.fixture
def capture_calls(monkeypatch):
    monkeypatch.setenv("HERDR_ENV", "1")
    monkeypatch.setenv("HERDR_PANE_ID", "pane")
    monkeypatch.setenv("HERDR_SOCKET_PATH", "socket")
    monkeypatch.setattr(
        capture.shutil, "which", lambda command: "/plugin/bin/herdr-pace"
    )
    calls = []
    monkeypatch.setattr(
        capture.subprocess, "run", lambda *args, **kwargs: calls.append((args, kwargs))
    )
    return calls


def test_capture_passes_only_completed_reply_fields(capture_calls):
    capture.handle(
        {"hook_event_name": "Stop", "reply_text": "Ready.", "tool_input": "irrelevant"}
    )
    arguments, options = capture_calls[0]
    assert arguments[0] == ["/plugin/bin/herdr-pace", "capture"]
    assert "Ready." in options["input"]
    assert "tool_input" not in options["input"]
    assert options["timeout"] == 0.5


def test_subagent_reply_is_not_captured(capture_calls):
    capture.handle({"hook_event_name": "SubagentStop", "reply_text": "Child"})
    capture.handle(
        {"hook_event_name": "Stop", "agent_id": "child", "reply_text": "Child"}
    )
    assert not capture_calls


def test_capture_timeout_never_blocks_stop(capture_calls, monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("capture", 0.5)

    monkeypatch.setattr(capture.subprocess, "run", timeout)
    assert capture.handle({"hook_event_name": "Stop", "reply_text": "Ready."}) is None


@pytest.mark.parametrize(
    "decision, captured",
    [(None, True), ("allow", True), ("block", False), ("deny", False)],
)
def test_only_accepted_stop_replies_are_captured(monkeypatch, decision, captured):
    dispatcher = import_hyphenated_hook_module("stop-dispatcher")
    calls = []
    monkeypatch.setattr(
        dispatcher,
        "dispatched_hook_input_or_exit",
        lambda events: {"hook_event_name": "Stop"},
    )
    monkeypatch.setattr(
        dispatcher,
        "run_handlers",
        lambda payload, handlers, surface: calls.append(handlers)
        or SimpleNamespace(decision=decision),
    )
    monkeypatch.setattr(dispatcher, "emit_stop_decision", lambda outcome: None)
    with pytest.raises(SystemExit):
        dispatcher.main()
    assert (dispatcher.COMPLETION_HANDLERS in calls) is captured
