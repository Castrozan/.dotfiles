import json
from datetime import UTC, datetime
from unittest.mock import Mock

import wake_listener
from conversation_addressee import Addressee
from listener_session import ListenerPurpose
from wake_fakes import IBARAKI, VOYAGER, armed_listener, boundaries
from wake_phrase import LiveSession


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


def test_addressing_another_session_hands_over_after_the_complete_turn():
    fakes, listener = conversation_with(Addressee(VOYAGER.pane, VOYAGER.servant, 0))
    entries = said("roda os testes", "hey Ibaraki, status", "e o build")
    entries[1]["turn_finished"] = False
    fakes.transcript_entries.return_value = entries[:2]
    listener.read_conversation()
    fakes.hand_to.assert_not_called()
    fakes.prompt_now.assert_not_called()
    fakes.transcript_entries.return_value = entries
    listener.read_conversation()
    assert fakes.hand_to.call_args.args[0] == Addressee(
        IBARAKI.pane, IBARAKI.servant, heard_through=3
    ), "the new session's follow starts after the words that named it"
    pane, text, _ = fakes.prompt_now.call_args.args
    assert pane == IBARAKI.pane and "status e o build" in text and "open" in text
    fakes.open_conversation.assert_not_called()


def test_naming_the_session_already_listening_changes_nothing():
    fakes, listener = conversation_with(Addressee(VOYAGER.pane, VOYAGER.servant, 0))
    fakes.transcript_entries.return_value = said("hey Voyager, keep going")
    listener.read_conversation()
    fakes.hand_to.assert_not_called()
    fakes.prompt_now.assert_not_called()


def test_each_conversation_turn_is_logged_and_matched_once():
    fakes, listener = conversation_with(None)
    text = "hey Ibaraki, revisão do build\ne da fila"
    fakes.transcript_entries.return_value = said(text)
    listener.read_conversation()
    fakes.addressee.return_value = Addressee(VOYAGER.pane, VOYAGER.servant, 0)
    listener.read_conversation()
    transcript, wake = [call.args[0] for call in fakes.report.call_args_list]
    assert "\n" not in transcript and "\r" not in transcript
    assert "revisão" in transcript
    record = json.loads(transcript)
    assert record["text"] == text
    assert record["phase"] == "conversation"
    assert record["sequence"] == 1
    assert record["source"] == "human"
    assert record["speaker"] is None
    assert datetime.fromisoformat(record["timestamp"]).tzinfo == UTC
    assert wake == f"wake {IBARAKI.servant} at {IBARAKI.pane}"
    assert fakes.prompt_now.call_count == 1


def test_turns_spoken_before_the_wake_joined_are_not_replayed():
    fakes = boundaries(
        transcript_entries=Mock(return_value=said("hey Ibaraki, status"))
    )
    listener = wake_listener.WakeListener(fakes, dry_run=False)
    listener.start_reading_conversation()
    listener.read_conversation()
    fakes.prompt_now.assert_not_called()


def test_a_restarted_conversation_discards_pending_speech_and_reads_new_turns():
    fakes, listener = conversation_with(None)
    entries = said("one", "two", "hey")
    entries[-1]["turn_finished"] = False
    fakes.transcript_entries.return_value = entries
    listener.read_conversation()
    fakes.transcript_entries.return_value = said("Ibaraki, status")
    listener.read_conversation()
    fakes.prompt_now.assert_not_called()
    fakes.transcript_entries.return_value = said(
        "Ibaraki, status", "hey Ibaraki, status"
    )
    listener.read_conversation()
    assert fakes.prompt_now.call_args.args[0] == IBARAKI.pane


def test_a_name_mention_in_the_last_fragment_keeps_the_current_servant():
    astolfo = LiveSession("Astolfo", "wW:pAS")
    fakes, listener = conversation_with(
        Addressee(VOYAGER.pane, VOYAGER.servant, 0), (VOYAGER, astolfo)
    )
    texts = ["I haven't said hey or something yet. Uh, I think", "Astolfo, Astolfo"]
    fakes.transcript_entries.return_value = [
        {"sequence": 16, "text": texts[0], "turn_finished": False},
        {"sequence": 17, "text": texts[1], "turn_finished": True},
    ]
    listener.read_conversation()
    fakes.hand_to.assert_not_called()
    fakes.prompt_now.assert_not_called()
    records = [json.loads(call.args[0]) for call in fakes.report.call_args_list]
    assert [(item["sequence"], item["text"]) for item in records] == list(
        zip((16, 17), texts, strict=True)
    )


def test_a_bare_name_opening_or_ending_a_turn_keeps_the_floor():
    fakes, listener = conversation_with(Addressee(VOYAGER.pane, VOYAGER.servant, 0))
    fakes.transcript_entries.return_value = said(
        "Ibaraki, status", "check the build, Ibaraki"
    )
    listener.read_conversation()
    fakes.sessions.assert_not_called()
    fakes.hand_to.assert_not_called()
    fakes.prompt_now.assert_not_called()


def test_the_avatar_echoing_a_name_is_logged_and_turns_nothing():
    fakes, listener = conversation_with(Addressee(VOYAGER.pane, VOYAGER.servant, 0))
    fakes.transcript_entries.return_value = [
        {"sequence": 1, "text": "hey Ibaraki", "source": "human", "speaker": "avatar"}
    ]
    listener.read_conversation()
    assert fakes.report.call_count == 1
    record = json.loads(fakes.report.call_args.args[0])
    assert record["speaker"] == "avatar"
    assert record["text"] == "hey Ibaraki"
    fakes.hand_to.assert_not_called()
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
        "hey Ibaraki, what do you think", source="meeting"
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
