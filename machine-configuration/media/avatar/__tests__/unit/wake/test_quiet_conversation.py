import os
import time
from unittest.mock import Mock

import listener_session
import pytest
import quiet_conversation
import wake_boundaries
import wake_listener
from conversation_seat import Seat
from listener_session import ListenerPurpose

LONG_QUIET = quiet_conversation.QUIET_CLOSE_SECONDS + 1


def boundaries(
    quiet_seconds,
    purpose=ListenerPurpose.CONVERSATION,
    seat=Seat.ROOM,
    call_ended=False,
):
    return wake_boundaries.Boundaries(
        quiet_seconds=Mock(return_value=quiet_seconds),
        listening_purpose=Mock(return_value=purpose),
        open_seat=Mock(return_value=seat),
        discord_call_ended=Mock(return_value=call_ended),
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


def test_a_discord_conversation_closes_when_the_listener_left_the_call():
    ended = boundaries(0.0, seat=Seat.DISCORD, call_ended=True)
    assert quiet_conversation.close_when_the_call_ended(ended) is True
    ended.close_conversation.assert_called_once_with()
    ended.report.assert_called_once_with(quiet_conversation.CALL_ENDED)


def test_a_discord_conversation_stays_open_while_the_listener_is_in_the_call():
    present = boundaries(0.0, seat=Seat.DISCORD, call_ended=False)
    assert quiet_conversation.close_when_the_call_ended(present) is False
    assert not present.close_conversation.called


@pytest.mark.parametrize("seat", [Seat.ROOM, Seat.REMOTE, None])
def test_only_a_discord_conversation_is_closed_for_the_call_ending(seat):
    other = boundaries(0.0, seat=seat, call_ended=True)
    assert quiet_conversation.close_when_the_call_ended(other) is False
    assert not other.close_conversation.called
    assert not other.discord_call_ended.called


def test_a_dry_run_closes_no_call():
    ended = boundaries(0.0, seat=Seat.DISCORD, call_ended=True)
    assert quiet_conversation.close_when_the_call_ended(ended, True) is False
    assert not ended.close_conversation.called


def test_the_loop_closes_an_ended_call_without_waiting_for_quiet(monkeypatch):
    following = boundaries(0.0, seat=Seat.DISCORD, call_ended=True)
    following.conversation_listening = Mock(side_effect=[True, False])
    following.transcript_entries = Mock(return_value=[])
    monkeypatch.setattr(quiet_conversation, "ARM_CHECK_SECONDS", 0)
    quiet_conversation.follow_conversation(wake_listener.WakeListener(following, False))
    following.close_conversation.assert_called_once_with()
    following.report.assert_called_once_with(quiet_conversation.CALL_ENDED)
