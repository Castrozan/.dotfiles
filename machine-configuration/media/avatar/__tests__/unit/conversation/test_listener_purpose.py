import argparse
import json
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import conversation_state
import listen_cli
import listener_session
import listener
import pytest
import conversation_effects
import user_units
import utterances
from conversation_state import ConversationPhase


def write_listener_configuration(directory, purpose):
    (directory / "listener.json").write_text(
        json.dumps({"purpose": purpose, "sources": {"human": "mic"}})
    )


def test_listening_refuses_while_the_conversation_listener_runs(tmp_path, monkeypatch):
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.OPEN
    )
    begin = Mock()
    monkeypatch.setattr(listener_session, "begin_listening", begin)
    with pytest.raises(ValueError, match="avatar-talk close"):
        listen_cli.start(SimpleNamespace(microphone=None, language=None), tmp_path)
    begin.assert_not_called()


def test_a_meeting_listener_is_not_an_open_conversation(tmp_path, monkeypatch):
    write_listener_configuration(tmp_path, listener_session.ListenerPurpose.MEETING)
    monkeypatch.setattr(user_units, "unit_active", lambda unit: True)
    monkeypatch.setattr(listener_session, "listening", lambda: True)
    assert conversation_state.observe(tmp_path) is ConversationPhase.MEETING


def test_beginning_a_listener_resets_the_transcript_and_the_heard_cursor(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(listener_session, "systemctl", Mock())
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text("{}")
    utterances.remember(tmp_path, 7)
    listener_session.begin_listening(
        tmp_path,
        listener_session.ListenerPurpose.MEETING,
        {"meeting": "any"},
        language="pt",
    )
    assert not transcript.exists()
    assert not (tmp_path / listener.HEARD_FILE).exists()
    assert utterances.last_heard(tmp_path) == 0
    configuration = json.loads((tmp_path / "listener.json").read_text())
    assert configuration == {
        "purpose": "meeting",
        "sources": {"meeting": "any"},
        "language": "pt",
    }


def test_hiding_the_window_hides_the_canvas_first(tmp_path, monkeypatch):
    order = []
    monkeypatch.setattr(
        conversation_effects.subprocess,
        "run",
        Mock(side_effect=lambda *a, **k: order.append("canvas")),
    )
    monkeypatch.setattr(
        conversation_effects.desktop_window, "hide", lambda: order.append("window")
    )
    conversation_effects.hide_window(argparse.Namespace(), tmp_path)
    assert order == ["canvas", "window"]


def test_a_failed_canvas_hide_leaves_the_window_where_it_is(tmp_path, monkeypatch):
    hide = Mock()
    monkeypatch.setattr(conversation_effects.desktop_window, "hide", hide)
    monkeypatch.setattr(
        conversation_effects.subprocess,
        "run",
        Mock(side_effect=subprocess.CalledProcessError(1, "avatar-command")),
    )
    with pytest.raises(subprocess.CalledProcessError):
        conversation_effects.hide_window(argparse.Namespace(), tmp_path)
    hide.assert_not_called()
