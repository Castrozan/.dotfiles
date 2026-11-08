import stat

import pytest
from orchestrator_cli import peer_messenger

FAKE_A2A_SCRIPT = """#!/bin/sh
printf '%s\\n' "$@" > "${0%/*}/arguments"
if [ "$1" = whoami ]; then
  if [ "$2" = --sender ]; then echo "$3"; else echo pane-servant; fi
  exit 0
fi
if [ "$2" = offline-peer ]; then echo "a2a: no peer named offline-peer" >&2; exit 1; fi
"""


@pytest.fixture
def fake_a2a(monkeypatch, tmp_path):
    executable = tmp_path / "a2a"
    executable.write_text(FAKE_A2A_SCRIPT)
    executable.chmod(executable.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", str(tmp_path))
    return tmp_path / "arguments"


def test_the_sender_comes_from_a2a_so_identity_rules_live_in_one_place(fake_a2a):
    assert peer_messenger.sender_name(None) == "pane-servant"
    assert peer_messenger.sender_name("Medea") == "Medea"
    assert fake_a2a.read_text().split() == ["whoami", "--sender", "Medea"]


def test_a_notification_passes_target_text_and_sender_to_a2a_notify(fake_a2a):
    peer_messenger.notify_peer("worker-pane", "Medea", "decision D-1\nanswered")
    assert (
        fake_a2a.read_text()
        == "notify\nworker-pane\ndecision D-1\nanswered\n--sender\nMedea\n"
    )


def test_a_refused_notification_keeps_the_saved_record_and_names_a2a_reason(
    fake_a2a, tmp_path, capsys
):
    saved_path = tmp_path / "D-1.json"
    exit_code = peer_messenger.notify_after_save(
        lambda: "Medea", "offline-peer", "decision D-1", saved_path
    )
    assert exit_code == 1
    error = capsys.readouterr().err
    assert f"{saved_path} is saved but offline-peer was not notified" in error
    assert "no peer named offline-peer" in error


def test_a_missing_a2a_command_is_a_message_failure_not_a_crash(monkeypatch, tmp_path):
    monkeypatch.setenv("PATH", str(tmp_path))
    with pytest.raises(peer_messenger.PeerMessageFailure):
        peer_messenger.sender_name(None)
