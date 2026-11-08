import json
import queue
import threading
from pathlib import Path
from unittest.mock import Mock

import listener_session
import conversation_effects
import listener
import source_capture

FRAME = b"\xb8\x0b" * 480
SILENT_FRAME = bytes(960)


def always_open():
    return True


def listening_with(tmp_path, interrupt=None):
    return listener.Listening(
        segments=queue.Queue(maxsize=1),
        stopping=threading.Event(),
        pending=listener.PendingSpeech(tmp_path / "marker"),
        interrupt_speaker=interrupt or Mock(),
    )


def test_a_pending_utterance_is_marked_until_every_part_finished(tmp_path):
    pending = listener.PendingSpeech(tmp_path / "marker")
    pending.begin()
    pending.begin()
    pending.finish()
    assert (tmp_path / "marker").exists()
    pending.finish()
    assert not (tmp_path / "marker").exists()


def test_a_stale_marker_from_a_killed_listener_is_cleared(tmp_path):
    (tmp_path / "marker").touch()
    listener.PendingSpeech(tmp_path / "marker")
    assert not (tmp_path / "marker").exists()


def test_sustained_speech_interrupts_the_speaker_once_per_segment(tmp_path):
    listening = listening_with(tmp_path)
    speech = source_capture.SourceSpeech("human", listening)
    for _ in range(40):
        speech.feed(FRAME)
    listening.interrupt_speaker.assert_called_once()


def test_a_short_noise_never_interrupts_and_leaves_nothing_pending(tmp_path):
    listening = listening_with(tmp_path)
    speech = source_capture.SourceSpeech("human", listening)
    for frame in [FRAME] * 3 + [SILENT_FRAME] * 40:
        speech.feed(frame)
    listening.interrupt_speaker.assert_not_called()
    assert not (tmp_path / "marker").exists()


def test_a_finished_segment_stays_pending_until_it_is_transcribed(tmp_path):
    listening = listening_with(tmp_path)
    speech = source_capture.SourceSpeech("human", listening)
    for frame in [FRAME] * 30 + [SILENT_FRAME] * 40:
        speech.feed(frame)
    assert listening.segments.qsize() == 1
    assert (tmp_path / "marker").exists()


def test_a_segment_dropped_for_a_full_queue_is_not_left_pending(tmp_path):
    listening = listening_with(tmp_path)
    listening.segments.put_nowait(("human", b"waiting", True))
    speech = source_capture.SourceSpeech("human", listening)
    for frame in [FRAME] * 30 + [SILENT_FRAME] * 40:
        speech.feed(frame)
    assert not (tmp_path / "marker").exists()


def test_capture_lost_mid_speech_leaves_nothing_pending(tmp_path):
    listening = listening_with(tmp_path)
    speech = source_capture.SourceSpeech("human", listening)
    speech.feed(FRAME)
    speech.abandon()
    assert not (tmp_path / "marker").exists()


def test_a_failed_segment_is_dropped_and_the_next_one_is_still_recorded(
    tmp_path, monkeypatch, capsys
):
    listening = listening_with(tmp_path)
    listening.segments = queue.Queue()
    listening.pending.begin()
    listening.pending.begin()
    listening.segments.put_nowait(("human", b"lost", True))
    listening.segments.put_nowait(("human", b"kept", True))
    transcribed = []

    def transcribe(segment, language):
        transcribed.append(segment)
        if segment == b"lost":
            raise TimeoutError("No transcriber answered")
        listening.stopping.set()
        return "oi"

    monkeypatch.setattr(listener, "transcribe_when_ready", transcribe)
    listener.write_transcript(tmp_path / "transcript.jsonl", listening)
    assert transcribed == [b"lost", b"kept"]
    assert capsys.readouterr().err == (
        "Dropped a human segment: No transcriber answered\n"
    )
    assert "oi" in (tmp_path / "transcript.jsonl").read_text()
    assert not (tmp_path / "marker").exists()


def test_the_requested_language_reaches_the_recognizer(tmp_path, monkeypatch):
    transcribe = Mock(return_value="oi")
    monkeypatch.setattr(
        listener.cloud_transcriber, "transcribe_with_local_fallback", transcribe
    )
    assert listener.transcribe_when_ready(b"pcm", "pt") == "oi"
    transcribe.assert_called_once_with(b"pcm", "pt")


def test_settings_reach_the_listener_configuration(tmp_path, monkeypatch):
    monkeypatch.setattr(listener_session, "systemctl", Mock())
    listener_session.begin_listening(
        tmp_path,
        "conversation",
        {"human": "AvatarRoomMicrophone"},
        language="pt",
        barge_in=True,
    )
    assert json.loads((tmp_path / "listener.json").read_text()) == {
        "purpose": "conversation",
        "sources": {"human": "AvatarRoomMicrophone"},
        "language": "pt",
        "barge_in": True,
    }


def test_the_room_microphone_cancels_everything_the_desktop_plays():
    configuration = (
        Path(__file__).resolve().parents[3] / "room-microphone.conf"
    ).read_text()
    assert "monitor.mode = true" in configuration
    assert f'"{conversation_effects.ROOM_MICROPHONE}"' in configuration
