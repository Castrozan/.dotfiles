import argparse
import json
import queue
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import conversation_seat
import conversation_state
import listener
import pytest
import remote_agent
import source_capture
import speech_segmenter
import transcript_log
import voice_turns
import wake_prompts
from conversation_state import ConversationPhase
from talk_runner import run_talk
from wake_phrase import LiveSession, WakeMatch

SPEECH = b"\xb8\x0b" * 480
SILENCE = bytes(960)
PANE = "wW:pSP"
CLOSING_SILENCE = (
    speech_segmenter.frames_for(speech_segmenter.TRAILING_SILENCE_SECONDS)
    * speech_segmenter.FRAME_SECONDS
)


def listening_with(tmp_path):
    return listener.Listening(
        segments=queue.Queue(),
        stopping=threading.Event(),
        pending=listener.PendingSpeech(tmp_path / "marker"),
        interrupt_speaker=Mock(),
        turn_finished=Mock(return_value=True),
    )


def records_of(report):
    return [json.loads(call.args[0]) for call in report.call_args_list]


def test_a_segment_carries_when_the_speech_ended_and_when_it_closed(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(source_capture, "time", SimpleNamespace(time=lambda: 100.0))
    listening = listening_with(tmp_path)
    speech = source_capture.SourceSpeech("human", listening)
    for frame in [SPEECH] * 30 + [SILENCE] * 40:
        speech.feed(frame)
    *_, heard = listening.segments.get_nowait()
    assert heard.segment_closed == 100.0
    assert heard.speech_ended == pytest.approx(100.0 - CLOSING_SILENCE)


def test_the_transcript_entry_keeps_every_listener_moment(tmp_path, monkeypatch):
    listening = listening_with(tmp_path)
    heard = source_capture.HeardMoments(speech_ended=10.0, segment_closed=10.69)
    listening.segments.put_nowait(("human", b"pcm", True, heard))
    monkeypatch.setattr(listener, "transcribe_when_ready", Mock(return_value="oi"))
    monkeypatch.setattr(listener, "time", SimpleNamespace(time=lambda: 11.0))
    listening.pending.begin()
    listening.pending.finish = Mock(side_effect=listening.stopping.set)
    listener.write_transcript(tmp_path / "transcript.jsonl", listening)
    (entry,) = transcript_log.read_since(tmp_path / "transcript.jsonl", 0)
    assert (entry["speech_ended"], entry["segment_closed"]) == (10.0, 10.69)
    assert entry["transcription_started"] == 11.0
    assert entry["time"] >= 11.0


def test_the_wake_log_copies_the_listener_moments_of_each_turn():
    report = Mock()
    entry = {"sequence": 4, "text": "oi", "time": 12.5, "turn_finished": False}
    entry |= {"speech_ended": 10.0, "segment_closed": 10.69}
    entry |= {"transcription_started": 11.0}
    transcript_log.report_conversation(report, entry)
    (record,) = records_of(report)
    assert {name: record[name] for name in entry if name != "time"} == {
        name: value for name, value in entry.items() if name != "time"
    }
    assert record["transcript_written"] == 12.5


def test_the_wake_logs_how_long_handing_the_prompt_took():
    boundaries = SimpleNamespace(
        report=Mock(),
        now=Mock(side_effect=[5.0, 5.25]),
        prompt_now=Mock(return_value=False),
        notify_at_idle=Mock(),
    )
    match = WakeMatch(LiveSession("Ibaraki-dōji", PANE), "status")
    assert wake_prompts.deliver(boundaries, False, match, "conversation", 7)
    delivery = json.loads(boundaries.report.call_args.args[0])
    assert delivery | {"timestamp": None, "room": None} == {
        "timestamp": None,
        "phase": "delivery",
        "room": None,
        "purpose": "conversation",
        "sequence": 7,
        "servant": "Ibaraki-dōji",
        "pane": PANE,
        "host": None,
        "delivered": wake_prompts.NOTIFIED_AT_IDLE,
        "delivery_ms": 250,
    }


def test_every_talk_command_is_logged_with_the_pane_that_ran_it(tmp_path, monkeypatch):
    report = Mock()
    monkeypatch.setattr(transcript_log, "report_to_log", report)
    monkeypatch.setenv(remote_agent.PANE_ENVIRONMENT_VARIABLE, PANE)
    monkeypatch.setattr(
        conversation_state, "observe", lambda directory: ConversationPhase.CLOSED
    )
    with pytest.raises(SystemExit):
        run_talk(monkeypatch, tmp_path, "show")
    (record,) = records_of(report)
    assert (record["phase"], record["action"], record["pane"]) == ("talk", "show", PANE)


def test_a_reply_logs_the_moments_the_control_server_acknowledged(
    tmp_path, monkeypatch, capsys
):
    acknowledgement = {"type": "speakAck", "status": "finished", "source": "kokoro"}
    acknowledgement["timing"] = {"received": 20_300, "synthesized": 21_000}
    acknowledgement["timing"] |= {"synthesisStarted": 20_310, "playing": 21_050}
    printed = json.dumps(acknowledgement) + "\n"
    runner = Mock(return_value=voice_turns.subprocess.CompletedProcess([], 0, printed))
    report = Mock()
    monkeypatch.setattr(voice_turns.subprocess, "run", runner)
    monkeypatch.setattr(transcript_log, "report_to_log", report)
    monkeypatch.setattr(voice_turns, "time", SimpleNamespace(time=lambda: 20.0))
    monkeypatch.setattr(conversation_seat, "current", lambda directory: "room")
    monkeypatch.setenv(remote_agent.PANE_ENVIRONMENT_VARIABLE, PANE)
    with pytest.raises(SystemExit):
        voice_turns.say(
            argparse.Namespace(text="oi", emotion="happy", voice=None), tmp_path
        )
    assert capsys.readouterr().out == printed
    (record,) = records_of(report)
    assert record | {"timestamp": None, "room": None} == {
        "timestamp": None,
        "phase": "speech",
        "room": None,
        "pane": PANE,
        "invoked": 20.0,
        "status": "finished",
        "source": "kokoro",
        "speech_received": 20.3,
        "synthesis_started": 20.31,
        "synthesized": 21.0,
        "playing": 21.05,
    }


def test_a_reply_without_an_acknowledgement_is_still_logged():
    assert voice_turns.acknowledgement("Avatar command timed out\n{oops\n") == {}
    assert voice_turns.speech_moments({}) == {}
