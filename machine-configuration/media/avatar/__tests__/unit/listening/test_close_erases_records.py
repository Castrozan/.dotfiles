import argparse
from types import SimpleNamespace
from unittest.mock import Mock

import conversation_addressee
import conversation_effects
import conversation_seat
import listener_session
import pytest
from conversation_addressee import Addressee
from conversation_seat import Seat


@pytest.fixture
def closing(tmp_path, monkeypatch):
    transcript_present_when_the_listener_stopped = []

    def run(command, **keywords):
        if command[:3] == ["systemctl", "--user", "stop"]:
            transcript_present_when_the_listener_stopped.append(
                (tmp_path / "transcript.jsonl").exists()
            )
        return SimpleNamespace(returncode=0, stdout="")

    monkeypatch.setattr(conversation_effects.subprocess, "run", run)
    monkeypatch.setattr(conversation_effects.user_units, "unit_active", lambda _: True)
    monkeypatch.setattr(conversation_effects, "hide_everywhere", Mock())
    monkeypatch.setattr(conversation_seat, "current", lambda directory: Seat.ROOM)
    return transcript_present_when_the_listener_stopped


def test_closing_a_linux_conversation_deletes_what_was_said(tmp_path, closing):
    for record in listener_session.SESSION_RECORDS:
        (tmp_path / record).write_text("private")
    conversation_addressee.hand_to(tmp_path, Addressee("w1:p1", "Sasaki Kojirou", 0))
    conversation_effects.close_conversation(argparse.Namespace(), tmp_path)
    assert [path.name for path in tmp_path.iterdir() if path.is_file()] == [
        conversation_addressee.LOCK_FILE
    ]
    assert closing == [True], "the records go only after the listener stopped"


def test_closing_a_conversation_with_nothing_recorded_succeeds(tmp_path, closing):
    conversation_effects.close_conversation(argparse.Namespace(), tmp_path)
    assert not (tmp_path / "transcript.jsonl").exists()
