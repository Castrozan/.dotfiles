import struct
from unittest.mock import Mock

import speech_segmenter
import wake_boundaries
import wake_listener
from conversation_addressee import Addressee
from wake_phrase import LiveSession

VOYAGER = LiveSession("Voyager", "wW:pPZ")
IBARAKI = LiveSession("Ibaraki-dōji", "wW:pPY")
FRAME_SAMPLES = int(speech_segmenter.SAMPLE_RATE * speech_segmenter.FRAME_SECONDS)


def frames(amplitude, count):
    return [struct.pack(f"<{FRAME_SAMPLES}h", *([amplitude] * FRAME_SAMPLES))] * count


def boundaries(heard="hey Voyager, check the build", sessions=(VOYAGER,), **changes):
    fakes = dict(
        sessions=Mock(return_value=list(sessions)),
        conversation_listening=Mock(return_value=False),
        transcribe=Mock(return_value=heard),
        open_conversation=Mock(return_value=True),
        prompt_now=Mock(return_value=True),
        notify_at_idle=Mock(),
        report=Mock(),
        now=Mock(return_value=0.0),
        transcript_entries=Mock(return_value=[]),
        addressee=Mock(return_value=None),
        hand_to=Mock(),
    )
    fakes.update(changes)
    return wake_boundaries.Boundaries(**fakes)


def armed_listener(fakes, dry_run=False):
    listener = wake_listener.WakeListener(fakes, dry_run=dry_run)
    listener.armed()
    return listener


def test_no_live_session_keeps_the_microphone_closed():
    assert not wake_listener.WakeListener(boundaries(sessions=()), False).armed()


def test_an_open_avatar_conversation_pauses_the_wake():
    fakes = boundaries(conversation_listening=Mock(return_value=True))
    assert not wake_listener.WakeListener(fakes, False).armed(), (
        "the conversation's own listener owns the room while it runs"
    )


def test_a_spoken_wake_prompts_the_named_session_before_opening_the_avatar():
    order = Mock()
    fakes = boundaries(
        prompt_now=order.prompt_now, open_conversation=order.open_conversation
    )
    order.prompt_now.return_value = True
    armed_listener(fakes).listen_while_armed(iter(frames(4000, 40) + frames(0, 40)))
    assert [call[0] for call in order.mock_calls] == [
        "prompt_now",
        "open_conversation",
    ], "the words reach the session at once; the avatar takes about 4 s to open"
    pane, text = order.prompt_now.call_args.args
    assert pane == VOYAGER.pane and "check the build" in text


def test_the_prompt_asks_for_a_non_blocking_voice_reply():
    fakes = boundaries()
    armed_listener(fakes).hear(b"segment")
    text = fakes.prompt_now.call_args.args[1]
    assert "avatar-talk say" in text and "avatar-talk follow" in text
    assert "avatar-talk ask" not in text, "ask blocks the session waiting for a reply"


def test_a_refused_prompt_falls_back_to_delivery_at_idle():
    fakes = boundaries(prompt_now=Mock(return_value=False))
    armed_listener(fakes).hear(b"segment")
    assert fakes.notify_at_idle.call_args.args[0] == VOYAGER.pane


def test_a_dry_run_reports_the_match_and_reaches_nobody():
    fakes = boundaries()
    armed_listener(fakes, dry_run=True).hear(b"segment")
    fakes.prompt_now.assert_not_called()
    fakes.open_conversation.assert_not_called()
    assert "Voyager" in fakes.report.call_args.args[0]


def test_unaddressed_speech_reaches_nobody():
    fakes = boundaries(heard="I think Voyager broke it")
    armed_listener(fakes).hear(b"segment")
    fakes.prompt_now.assert_not_called()
    fakes.open_conversation.assert_not_called()


def test_listening_stops_once_the_fleet_is_gone():
    fakes = boundaries()
    listener = armed_listener(fakes)
    fakes.sessions.return_value = []
    fakes.now.return_value = wake_listener.FLEET_REFRESH_SECONDS
    assert not listener.listen_while_armed(
        iter(frames(0, wake_listener.FRAMES_PER_ARM_CHECK))
    )
    fakes.transcribe.assert_not_called()


def test_the_fleet_is_read_once_a_minute_while_quiet():
    fakes = boundaries()
    listener = armed_listener(fakes)
    for second in range(0, wake_listener.FLEET_REFRESH_SECONDS, 5):
        fakes.now.return_value = float(second)
        listener.armed()
    assert fakes.sessions.call_count == 1, "herdr pane list is too costly to poll often"


def test_names_are_reread_before_each_heard_utterance_is_matched():
    fakes = boundaries()
    listener = armed_listener(fakes)
    fakes.sessions.return_value = [LiveSession("Medea", "wW:pQQ")]
    fakes.transcribe.return_value = "hey Medea, status"
    listener.hear(b"segment")
    assert fakes.prompt_now.call_args.args[0] == "wW:pQQ", (
        "a session launched since the last poll is reachable at once"
    )


def test_a_failed_transcription_is_dropped_and_listening_continues():
    fakes = boundaries(transcribe=Mock(side_effect=ConnectionError("Hex refused")))
    armed_listener(fakes).hear(b"segment")
    assert "Hex refused" in fakes.report.call_args.args[0]
    fakes.prompt_now.assert_not_called()


def test_the_prompt_never_claims_who_spoke():
    fakes = boundaries()
    armed_listener(fakes).hear(b"segment")
    text = fakes.prompt_now.call_args.args[1]
    assert "not verified" in text and "Lucas" not in text, (
        "anyone in the room can speak a name, so the agent must not assume its owner"
    )


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
