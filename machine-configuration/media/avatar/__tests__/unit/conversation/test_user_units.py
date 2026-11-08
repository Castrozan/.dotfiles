import json
from types import SimpleNamespace
from unittest.mock import Mock

import conversation_state
import pytest
import user_units
from conversation_state import ConversationPhase

ACTIVE, UNREACHABLE, INACTIVE, MISSING = 0, 1, 3, 4


def systemctl_answering(monkeypatch, *exit_codes):
    run = Mock(side_effect=[SimpleNamespace(returncode=code) for code in exit_codes])
    monkeypatch.setattr(user_units.subprocess, "run", run)
    monkeypatch.setattr(user_units.time, "sleep", Mock())
    return run


def test_a_rebuild_reexecuting_systemd_does_not_close_the_conversation(monkeypatch):
    run = systemctl_answering(monkeypatch, UNREACHABLE, UNREACHABLE, ACTIVE)
    assert user_units.unit_active("avatar-conversation.target") is True
    assert run.call_count == 3


@pytest.mark.parametrize("exit_code", [INACTIVE, MISSING])
def test_a_stopped_unit_is_reported_at_once(monkeypatch, exit_code):
    run = systemctl_answering(monkeypatch, exit_code)
    assert user_units.unit_active("avatar-listener.service") is False
    assert run.call_count == 1


def test_systemd_unreachable_past_the_retry_window_counts_as_stopped(monkeypatch):
    systemctl_answering(monkeypatch, UNREACHABLE, UNREACHABLE)
    clock = iter([0, 0, user_units.UNREACHABLE_RETRY_SECONDS + 1])
    monkeypatch.setattr(user_units.time, "monotonic", lambda: next(clock))
    assert user_units.unit_active("avatar-listener.service") is False


def test_an_open_conversation_needs_both_the_target_and_the_listener(
    tmp_path, monkeypatch
):
    (tmp_path / "listener.json").write_text(
        json.dumps({"purpose": "conversation", "sources": {}})
    )
    systemctl_answering(monkeypatch, UNREACHABLE, ACTIVE, UNREACHABLE, ACTIVE)
    assert conversation_state.observe(tmp_path) is ConversationPhase.OPEN
