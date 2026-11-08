from unittest.mock import Mock

import wake_listener
from conversation_addressee import Addressee
from listener_session import ListenerPurpose
from wake_fakes import IBARAKI, VOYAGER, armed_listener, boundaries


def said(*texts, source="human"):
    return [
        {"sequence": sequence, "text": text, "source": source}
        for sequence, text in enumerate(texts, start=1)
    ]


def conversation_with(addressee, sessions=(VOYAGER, IBARAKI)):
    fakes = boundaries(
        sessions=sessions,
        addressee=Mock(return_value=addressee),
        conversation_listening=Mock(return_value=True),
    )
    listener = wake_listener.WakeListener(fakes, dry_run=False)
    listener.start_reading_conversation()
    return fakes, listener


def test_a_wake_hands_the_conversation_it_opens_to_the_woken_session():
    order = Mock()
    fakes = boundaries(open_conversation=order.open, hand_to=order.hand_to)
    armed_listener(fakes).hear(b"segment")
    assert [call[0] for call in order.mock_calls] == ["open", "hand_to"]
    assert order.hand_to.call_args.args[0] == Addressee(
        VOYAGER.pane, VOYAGER.servant, heard_through=0
    )


def test_naming_another_session_mid_conversation_turns_the_room_to_it():
    fakes, listener = conversation_with(Addressee(VOYAGER.pane, VOYAGER.servant, 0))
    fakes.transcript_entries.return_value = said(
        "roda os testes", "hey Ibaraki, status"
    )
    listener.read_conversation()
    assert fakes.hand_to.call_args.args[0] == Addressee(
        IBARAKI.pane, IBARAKI.servant, heard_through=2
    ), "the new session's follow starts after the words that named it"
    pane, text = fakes.prompt_now.call_args.args
    assert pane == IBARAKI.pane and "status" in text and "open" in text
    fakes.open_conversation.assert_not_called()


def test_naming_the_session_already_listening_changes_nothing():
    fakes, listener = conversation_with(Addressee(VOYAGER.pane, VOYAGER.servant, 0))
    fakes.transcript_entries.return_value = said("hey Voyager, keep going")
    listener.read_conversation()
    fakes.hand_to.assert_not_called()
    fakes.prompt_now.assert_not_called()


def test_each_conversation_turn_is_matched_once():
    fakes, listener = conversation_with(None)
    fakes.transcript_entries.return_value = said("hey Ibaraki, status")
    listener.read_conversation()
    fakes.addressee.return_value = Addressee(VOYAGER.pane, VOYAGER.servant, 0)
    listener.read_conversation()
    assert fakes.prompt_now.call_count == 1


def test_turns_spoken_before_the_wake_joined_are_not_replayed():
    fakes = boundaries(
        transcript_entries=Mock(return_value=said("hey Ibaraki, status"))
    )
    listener = wake_listener.WakeListener(fakes, dry_run=False)
    listener.start_reading_conversation()
    listener.read_conversation()
    fakes.prompt_now.assert_not_called()


def test_a_restarted_conversation_is_read_from_its_first_turn():
    fakes, listener = conversation_with(None)
    fakes.transcript_entries.return_value = said("one", "two", "three")
    listener.read_conversation()
    fakes.transcript_entries.return_value = said("hey Ibaraki, status")
    listener.read_conversation()
    assert fakes.prompt_now.call_args.args[0] == IBARAKI.pane


def test_turns_without_a_leading_greeting_reuse_the_fleet_read_this_minute():
    fakes, listener = conversation_with(None)
    listener.refresh_sessions()
    fakes.sessions.reset_mock()
    fakes.transcript_entries.return_value = said(
        "I think Ibaraki broke it", "roda os testes"
    )
    listener.read_conversation()
    fakes.sessions.assert_not_called()
    fakes.prompt_now.assert_not_called()


def test_a_name_opening_a_turn_without_a_greeting_turns_the_room():
    fakes, listener = conversation_with(Addressee(VOYAGER.pane, VOYAGER.servant, 0))
    fakes.transcript_entries.return_value = said("Ibaraki, status")
    listener.read_conversation()
    assert fakes.hand_to.call_args.args[0].pane == IBARAKI.pane, (
        "the floor moves on the same words, so the session it moves to must hear them"
    )
    assert fakes.prompt_now.call_args.args[0] == IBARAKI.pane


def test_the_avatar_echoing_a_name_turns_nothing():
    fakes, listener = conversation_with(Addressee(VOYAGER.pane, VOYAGER.servant, 0))
    fakes.transcript_entries.return_value = [
        {"sequence": 1, "text": "hey Ibaraki", "source": "human", "speaker": "avatar"}
    ]
    listener.read_conversation()
    fakes.prompt_now.assert_not_called()


def test_a_failed_handover_is_reported_and_reading_continues():
    fakes, listener = conversation_with(None)
    fakes.prompt_now.side_effect = TimeoutError("herdr hung")
    fakes.transcript_entries.return_value = said("hey Ibaraki, status")
    listener.read_conversation()
    assert "herdr hung" in fakes.report.call_args.args[0]


def test_a_voice_from_the_meeting_moves_the_floor_but_prompts_nobody():
    fakes, listener = conversation_with(Addressee(VOYAGER.pane, VOYAGER.servant, 0))
    fakes.transcript_entries.return_value = said(
        "Ibaraki, what do you think", source="meeting"
    )
    listener.read_conversation()
    assert fakes.hand_to.call_args.args[0].pane == IBARAKI.pane
    fakes.prompt_now.assert_not_called()


def test_a_session_named_during_a_meeting_is_told_to_answer_the_meeting():
    fakes, listener = conversation_with(Addressee(VOYAGER.pane, VOYAGER.servant, 0))
    fakes.listening_purpose.return_value = ListenerPurpose.MEETING
    fakes.transcript_entries.return_value = said("hey Ibaraki, status")
    listener.read_conversation()
    text = fakes.prompt_now.call_args.args[1]
    assert "avatar-command speak" in text and "avatar-talk" not in text, (
        "avatar-talk refuses while a meeting is transcribed"
    )


def test_naming_a_session_in_a_live_conversation_moves_the_floor_without_a_prompt():
    fakes, listener = conversation_with(Addressee(VOYAGER.pane, VOYAGER.servant, 0))
    fakes.listening_purpose.return_value = ListenerPurpose.LIVE
    fakes.transcript_entries.return_value = said("hey Ibaraki, status")
    listener.read_conversation()
    assert fakes.hand_to.call_args.args[0].pane == IBARAKI.pane
    assert not fakes.prompt_now.called, "the live bridge routes the task itself"
