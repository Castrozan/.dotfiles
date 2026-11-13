import struct
import subprocess
from unittest.mock import Mock

import speech_segmenter
import wake_listener
from wake_fakes import VOYAGER, armed_listener, boundaries
from wake_phrase import LiveSession

FRAME_SAMPLES = int(speech_segmenter.SAMPLE_RATE * speech_segmenter.FRAME_SECONDS)


def frames(amplitude, count):
    return [struct.pack(f"<{FRAME_SAMPLES}h", *([amplitude] * FRAME_SAMPLES))] * count


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


def test_the_prompt_tells_the_agent_to_close_when_dismissed():
    fakes = boundaries()
    armed_listener(fakes).hear(b"segment")
    text = fakes.prompt_now.call_args.args[1]
    assert "avatar-talk close" in text, "closing hands the room back to the wake"


def test_a_busy_transcriber_is_asked_again_until_it_answers():
    busy = [
        ConnectionError("Hex refused the segment: queue-full"),
        subprocess.CalledProcessError(1, ["ssh", "chise", "avatar-transcribe"]),
        "hey Voyager, check the build",
    ]
    fakes = boundaries(transcribe=Mock(side_effect=busy))
    armed_listener(fakes).hear(b"segment")
    assert fakes.transcribe.call_count == 3
    assert [call.args for call in fakes.pause.call_args_list] == [
        (wake_listener.TRANSCRIBER_RETRY_SECONDS,)
    ] * 2
    assert fakes.prompt_now.call_args.args[0] == VOYAGER.pane
    fakes.report.assert_called_once_with(f"wake Voyager at {VOYAGER.pane}")


def test_a_transcriber_that_never_answers_drops_the_utterance_after_a_bounded_wait():
    fakes = boundaries(transcribe=Mock(side_effect=ConnectionError("queue-full")))
    armed_listener(fakes).hear(b"segment")
    assert fakes.transcribe.call_count == wake_listener.TRANSCRIBER_ATTEMPTS
    assert fakes.pause.call_count == wake_listener.TRANSCRIBER_ATTEMPTS - 1
    fakes.report.assert_called_once_with("Dropped an utterance: queue-full")
    fakes.prompt_now.assert_not_called()
