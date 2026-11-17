import os
import time
from unittest.mock import Mock

import listener_session
import pytest
import quiet_conversation
import wake_boundaries
import wake_listener
from listener_session import ListenerPurpose

LONG_QUIET = quiet_conversation.QUIET_CLOSE_SECONDS + 1


def boundaries(quiet_seconds, purpose=ListenerPurpose.CONVERSATION):
    return wake_boundaries.Boundaries(
        quiet_seconds=Mock(return_value=quiet_seconds),
        listening_purpose=Mock(return_value=purpose),
        close_conversation=Mock(),
        report=Mock(),
    )


def test_a_conversation_the_avatar_left_quiet_is_closed_and_reported():
    quiet = boundaries(LONG_QUIET)
    assert quiet_conversation.close_when_quiet(quiet) is True
    quiet.close_conversation.assert_called_once_with()
    quiet.report.assert_called_once_with(quiet_conversation.CLOSING)


def test_a_conversation_the_avatar_spoke_in_lately_stays_open_unasked():
    lively = boundaries(quiet_conversation.QUIET_CLOSE_SECONDS - 1)
    assert quiet_conversation.close_when_quiet(lively) is False
    assert not lively.close_conversation.called
    assert not lively.listening_purpose.called


@pytest.mark.parametrize(
    "purpose", [ListenerPurpose.MEETING, ListenerPurpose.LIVE, None]
)
def test_only_a_plain_conversation_is_closed_for_quiet(purpose):
    other = boundaries(LONG_QUIET, purpose)
    assert quiet_conversation.close_when_quiet(other) is False
    assert not other.close_conversation.called


def aged(path, seconds):
    then = time.time() - seconds
    os.utime(path, (then, then))


def test_quiet_is_measured_from_the_opening_until_the_avatar_speaks(tmp_path):
    assert listener_session.quiet_seconds(tmp_path) == 0.0
    configuration = tmp_path / listener_session.CONFIGURATION_FILE
    configuration.write_text("{}")
    aged(configuration, 900)
    assert listener_session.quiet_seconds(tmp_path) == pytest.approx(900, abs=5)
    listener_session.mark_spoken(tmp_path)
    assert listener_session.quiet_seconds(tmp_path) == pytest.approx(0, abs=5)


def test_the_wake_checks_for_quiet_each_time_it_finds_the_conversation_open(
    monkeypatch,
):
    listening = Mock(side_effect=[True, False])
    following = boundaries(LONG_QUIET)
    following.conversation_listening = listening
    following.transcript_entries = Mock(return_value=[])
    monkeypatch.setattr(quiet_conversation, "ARM_CHECK_SECONDS", 0)
    quiet_conversation.follow_conversation(wake_listener.WakeListener(following, False))
    following.close_conversation.assert_called_once_with()


def test_a_dry_run_closes_nothing(monkeypatch):
    following = boundaries(LONG_QUIET)
    following.conversation_listening = Mock(side_effect=[True, False])
    following.transcript_entries = Mock(return_value=[])
    monkeypatch.setattr(quiet_conversation, "ARM_CHECK_SECONDS", 0)
    quiet_conversation.follow_conversation(wake_listener.WakeListener(following, True))
    assert not following.close_conversation.called
