import subprocess
from types import SimpleNamespace

import pytest

import chrome_devtools_cleanup_handler as cleanup


@pytest.mark.parametrize(
    "payload",
    [
        {"hook_event_name": "SubagentStop"},
        {"hook_event_name": "Stop", "agent_id": "child"},
        {},
    ],
)
def test_subagents_and_other_events_do_not_close_parent_browser(monkeypatch, payload):
    monkeypatch.setattr(
        cleanup.shutil,
        "which",
        lambda command: pytest.fail("looked up a cleanup command"),
    )
    assert cleanup.handle(payload) is None


def test_unavailable_cli_has_no_cleanup_side_effect(monkeypatch):
    monkeypatch.setattr(cleanup.shutil, "which", lambda command: None)
    assert cleanup.handle({"hook_event_name": "Stop"}) is None


def test_completion_uses_owned_cleanup_without_starting_browser(monkeypatch):
    monkeypatch.setattr(cleanup.shutil, "which", lambda command: "/bin/chrome-devtools")
    calls = []
    monkeypatch.setattr(
        cleanup.subprocess,
        "run",
        lambda arguments, **options: calls.append(arguments)
        or SimpleNamespace(returncode=0),
    )
    assert cleanup.handle({"hook_event_name": "Stop"}) is None
    assert calls == [
        ["/bin/chrome-devtools", "cleanup", "--keep-attached-for", "1800"]
    ]


def test_cleanup_failure_blocks_false_completion(monkeypatch):
    monkeypatch.setattr(cleanup.shutil, "which", lambda command: "/bin/chrome-devtools")
    monkeypatch.setattr(
        cleanup.subprocess,
        "run",
        lambda *arguments, **options: SimpleNamespace(
            returncode=1, stderr="worker is still running"
        ),
    )
    result = cleanup.handle({"hook_event_name": "Stop"})
    assert result.decision == "block"
    assert "worker is still running" in result.reason


def test_cleanup_timeout_blocks_false_completion(monkeypatch):
    monkeypatch.setattr(cleanup.shutil, "which", lambda command: "/bin/chrome-devtools")

    def timed_out(*arguments, **options):
        raise subprocess.TimeoutExpired("chrome-devtools", 25)

    monkeypatch.setattr(cleanup.subprocess, "run", timed_out)
    assert cleanup.handle({"hook_event_name": "Stop"}).decision == "block"
