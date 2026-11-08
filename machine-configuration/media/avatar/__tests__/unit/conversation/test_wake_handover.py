from unittest.mock import Mock

import wake_listener
from conversation_addressee import Addressee
from wake_fakes import IBARAKI, VOYAGER, armed_listener, boundaries


def said(*texts):
    return [
        {"sequence": sequence, "text": text}
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


def test_turns_without_a_leading_greeting_never_read_the_fleet():
    fakes, listener = conversation_with(None)
    fakes.sessions.reset_mock()
    fakes.transcript_entries.return_value = said("Ibaraki broke it", "roda os testes")
    listener.read_conversation()
    fakes.sessions.assert_not_called()


def test_a_failed_handover_is_reported_and_reading_continues():
    fakes, listener = conversation_with(None)
    fakes.prompt_now.side_effect = TimeoutError("herdr hung")
    fakes.transcript_entries.return_value = said("hey Ibaraki, status")
    listener.read_conversation()
    assert "herdr hung" in fakes.report.call_args.args[0]
